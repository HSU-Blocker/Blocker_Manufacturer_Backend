from app import create_app

app = create_app()  # 실제 애플리케이션 인스턴스 생성

if __name__ == "__main__":
    app.run()