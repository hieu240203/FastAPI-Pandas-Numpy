from pydantic import BaseModel

class Book(BaseModel):
    Namebook: str
    Author: str
    Price: float
    Discount: int
    Rating: int
    Quantity: int
    Sell: int
    Status : str
    summary: str
    class Config: 
        orm_mode=True
        schema_extra={
            'example':{
                "Namebook": "Tâm lý học về tiền",
                "Author":"Morgan Housel",
                "Price": 113000,
                "Discount": 25,
                "Rating": 4,
                "Quantity": 24,
                "Sell" : 120,
                "Status": "Còn hàng",
                "summary": "Cuốn sách giúp chúng ta tránh khỏi những sai lầm về tiền bạc, cải thiện rất nhiều về việc đầu tư và phát triển lĩnh vực tài chính cá nhân",
            }
        }