from flask import Blueprint, jsonify, request
from .services.blockchain_service import BlockchainService

# Blueprint 인스턴스를 여기서 생성
bp = Blueprint('main', __name__)  # ✅ 변경된 부분
blockchain = BlockchainService()


# 프론트엔드와 엔드포인트 일치시키기
@bp.route('/api/blockchain/upload', methods=['POST'])
def handle_upload():
    try:
        data = request.get_json()
        
        # 1. JSON 파싱 실패 체크
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
            
        # 2. 필수 필드 검증
        if 'text' not in data:
            return jsonify({"error": "'text' field is required"}), 400
            
        input_text = data['text']
        print(f"Received valid text: {input_text}")
        
        # 3. 서비스 호출
        tx_hash = blockchain.upload_to_blockchain(input_text)
        
        return jsonify({
            "status": "success",
            "tx_hash": tx_hash,
            "received_text": input_text
        }), 200
        
    except ValueError as e:  # 서비스 계층 에러 캐치
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500