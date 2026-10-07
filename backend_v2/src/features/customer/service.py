from sqlalchemy.orm import Session

from src.core.models import Customer

from . import schemas


def get_all_customers(db: Session):
    return db.query(Customer).all()

def get_customer_by_id(db: Session, customer_id: int):
    return db.query(Customer).filter(Customer.id == customer_id).first()

def get_customer_by_code(db: Session, code: str):
    return db.query(Customer).filter(Customer.code == code).first()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = Customer(code=customer.code, name=customer.name)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def update_customer(db: Session, customer_id: int, customer: schemas.CustomerUpdate):
    db_customer = get_customer_by_id(db, customer_id)
    if not db_customer:
        return None
    
    update_data = customer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)
    
    db.commit()
    db.refresh(db_customer)
    return db_customer

def delete_customer(db: Session, customer_id: int):
    db_customer = get_customer_by_id(db, customer_id)
    if not db_customer:
        return False
    
    db.delete(db_customer)
    db.commit()
    return True
