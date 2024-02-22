from database import Base 
from sqlalchemy import String, Integer, Column, Boolean, Text, Double, Float, Sequence


class Books(Base):
    __tablename__ = 'books'
    ID = Column(Integer, Sequence('books_id_seq'), primary_key=True) # ID của cuốn sách
    Namebook = Column(String(100), unique= False, nullable= False) # Tên cuốn sách
    Author = Column(String(100), unique= False, nullable= True) # Tên tác giả
    Price = Column(Float, unique= False, nullable= True) # Giá của cuốn sách
    Discount = Column(Integer, unique= False, nullable= True) # Cuốn sách được giảm giá bao nhiêu phần trăm
    Rating = Column(Integer, unique= False, nullable= True) # Cuốn sách được đánh giá bao nhiêu sao 
    Quantity = Column(Integer, unique= False, nullable= False) # Số lượng cuốn sách còn trong shop
    Sell = Column(Integer,unique= False, nullable= True) # Cuốn sách đó đã bán được bao nhiêu quyển
    Status  = Column(String(50), unique= False, nullable= False) # Trạng thái của cuốn sách có 2 sự lựa chọn Còn hàng hoặc hết hàng
    summary = Column(String(2000), unique= False, nullable= True) # tóm tắt nội dung của cuốn sách
