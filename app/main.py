from fastapi import FastAPI

from app.routes.products import ProductStore, router


def create_app() -> FastAPI:
    application = FastAPI(title="Products CI/CD Demo", version="1.0.0")
    application.state.store = ProductStore()
    application.include_router(router)

    @application.get("/")
    def root():
        return {"message": "Welcome to the Products API"}

    @application.get("/health")
    def health():
        return {"status": "ok"}

    return application


app = create_app()
