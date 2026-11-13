from threading import Lock

from fastapi import APIRouter, HTTPException, Path, Request, Response, status

from app.models import Product, ProductCreate

router = APIRouter(prefix="/products", tags=["Products"])


class ProductStore:
    def __init__(self):
        self.products: dict[int, Product] = {}
        self.next_id = 1
        self.lock = Lock()


@router.get("", response_model=list[Product])
def list_products(request: Request):
    store = request.app.state.store
    with store.lock:
        return list(store.products.values())


@router.post("", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, request: Request):
    store = request.app.state.store
    with store.lock:
        product = Product(id=store.next_id, **payload.model_dump())
        store.products[product.id] = product
        store.next_id += 1
        return product


@router.get("/{id}", response_model=Product)
def get_product(request: Request, id: int = Path(gt=0)):
    store = request.app.state.store
    with store.lock:
        if id not in store.products:
            raise HTTPException(status_code=404, detail="Product not found")
        return store.products[id]


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(request: Request, id: int = Path(gt=0)):
    store = request.app.state.store
    with store.lock:
        if id not in store.products:
            raise HTTPException(status_code=404, detail="Product not found")
        del store.products[id]
    return Response(status_code=204)
