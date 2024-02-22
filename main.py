from fastapi import FastAPI, HTTPException, Depends, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError
import model 
from model import Books
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from schemas import Book
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt


app = FastAPI(
    title="API",
    description="This is a sample API ",
    openapi_url="/api/openapi.json",  # Đặt URL cho tệp OpenAPI JSON
    docs_url="/api/docs",  # Đặt URL cho Swagger UI
    )

model.Base.metadata.create_all(bind=engine)
Book_list = pd.DataFrame()

@app.get('/', description='Home page')
async def hello():
    return "Chào mừng bạn đến vớt hệ thống quản lý sách"

async def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# hàm lấy dữ liệu
def get_data(db):
    try:
        con = sqlite3.connect("data.db")  
        cursor = con.cursor()
        cursor.execute("SELECT * FROM books")  
        books = cursor.fetchall()

        if not books:
            raise HTTPException(status_code=406, detail='Dữ liệu chưa được tải lên')
        Book_list = pd.read_sql_query("SELECT * FROM books", con)
        columns_to_convert = ['ID', 'Price', 'Discount', 'Quantity', 'Rating', "Sell"]

        for col in columns_to_convert:
            try:
                Book_list[col] = Book_list[col].astype('int32') if Book_list[col].dtype == 'O' else Book_list[col].astype('float32')
            except (KeyError, ValueError) as e:
                raise HTTPException(status_code=500, detail=f"Error converting '{col}' column data: {str(e)}")
            
        con.close()
        return Book_list.to_dict(orient='records')
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"SQLite error: {str(e)}")


# post - pandas
@app.post('/books/uploadfile', status_code=201, description='Tải lên file dữ liệu (Đầu vào: File .csv - Đầu ra: Thông báo trạng thái dữ liệu đã được tải lên)')
async def create_upload_file(file: UploadFile,db: Session = Depends(get_db)):
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file.file)
        df.insert(0, 'ID', range(1, len(df) + 1))
        df.to_sql('books', db.bind, if_exists='replace', index=False)
        return {'message': 'Dữ liệu đã được tải lên thành công'}
    
    else:
        raise HTTPException(status_code=400, detail="Tệp không hợp lệ. Chỉ chấp nhận tệp CSV.")

# get - pandas
@app.get('/books/all', status_code=200, description='In ra tất cả sách trong shop (Đầu vào: None - Đầu ra: Dictionary, toàn bộ dữ liệu trong cơ sở dữ liệu)')
async def get_all_books(db: Session = Depends(get_db)):
    return get_data(db)
    
# post - pandas
@app.post('/books/addrow', status_code=201, description='Thêm một đối tượng vào dữ liệu (Đầu vào: Người dùng tự nhập dữ liệu - Đầu ra: Thông báo trạng thái)')
async def add_row_book(book: Book, db: Session = Depends(get_db)):
    try:
        Book_list = get_data(db) 
        df = pd.DataFrame(Book_list)
        new_row = pd.DataFrame({'ID': [len(df) + 1], 'Namebook': [book.Namebook], 'Author': [book.Author], 'Price': [book.Price], 'Discount': [book.Discount],'Rating': [book.Rating], 'Quantity': [book.Quantity],'Sell': [book.Sell], 'Status': [book.Status], 'summary': [book.summary]})
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_sql('books', db.bind, if_exists='replace', index=False)
        return {'message': 'Đã thêm một đối tượng vào dữ liệu'}
    except KeyError:
        raise HTTPException(status_code=400, detail='Cột không tồn tại')
    except ValueError:
        raise HTTPException(status_code=400, detail='Giá trị dữ liệu không hợp lệ')
    except TypeError:
        raise HTTPException(status_code=400, detail='Kiểu dữ liệu không khớp')

# put - pandas
@app.put('/books/update_book/{book_id}', status_code= 201, description= 'Thay đổi dữ liệu của một cuốn sách() (Đầu vào: Người dùng tự nhập dữ liệu mới cho một cuốn sách thông qua book_id Đầu ra: thông báo nội dung của cuốn sách đã được thay đổi)')
def update_book(book_id: int, book: Book, db: Session = Depends(get_db)):
        Book_list = get_data(db)
        df = pd.DataFrame(Book_list)
        mask = df['ID'] == book_id
        if mask.any():
            try: 
                df.loc[mask, 'Namebook'] = book.Namebook
                df.loc[mask, 'Author'] = book.Author
                df.loc[mask, 'Price'] = book.Price
                df.loc[mask, 'Discount'] = book.Discount
                df.loc[mask, 'Rating'] = book.Rating
                df.loc[mask, 'Quantity'] = book.Quantity
                df.loc[mask, 'Sell'] = book.Sell
                df.loc[mask, 'Status'] = book.Status
                df.loc[mask, 'summary'] = book.summary
                df.to_sql('books', db.bind, if_exists='replace', index=False)
                return {'message': 'Đã update dữ liệu cho một đối tượng vào dữ liệu'}
            except Exception as e: 
                raise HTTPException(status_code=500, detail=f'Đã xảy ra lỗi khi thay đổi dữ liệu của cuốn sách: {str(e)}')
        else:
            raise HTTPException(status_code=404, detail=f"Cuốn sách với ID {book_id} không tồn tại.")

# delete - numpy - xóa một dòng dữ liệu
@app.delete('/books/delete_row/{book_id}',status_code= 201, description="Xóa một cuốn sách khỏi cơ sở dữ liệu (đầu vào: id của một cuốn sách - đầu ra: thông báo cuốn sách đã được xóa hay chưa)")
async def delete_book(book_id : int , db: Session = Depends(get_db)):
    Book_list = get_data(db)
    df = pd.DataFrame(Book_list)
    if not df['ID'].isin([book_id]).any():
        raise HTTPException(status_code=404, detail=f"Cuốn sách với ID {book_id} không tồn tại.")
    df.drop([(book_id - 1)], inplace = True)
    df['ID'] = np.arange(1, len(df) + 1)
    df.to_sql('books', db.bind, if_exists='replace', index=False)
    return {'message': 'Đã xóa một đối tượng khỏi dữ liệu'}

# Max/Min/Median values
def calculate_statistics(data , column_name: str):
    if not pd.api.types.is_numeric_dtype(data[column_name]):
        if not set(data[column_name].unique()).issubset([0, 1]):
            raise HTTPException(status_code=400, detail='Kiểu dữ liệu của cột phải là số')

    mean = np.mean(data[column_name])    
    median = np.median(data[column_name]).astype(float)
    min_value = np.min(data[column_name])
    max_value = np.max(data[column_name])
    return {
        f'Trung bình_{column_name}': mean,
        f'Trung vị_{column_name}': median,
        f'Nhỏ nhất_{column_name}': min_value,
        f'Lớn nhất_{column_name}': max_value
    }

# get - numpy
@app.get('/books/statistic/{column}', status_code=200, description='In ra số liệu thống kê (Trung bình/ Trung vị/ Nhỏ nhất/ Lớn nhất) của 1 cột cụ thể (Đầu vào: String, tên cột - Đầu ra: Float, giá trị Trung bình/ Trung vị/ Nhỏ nhất/ Lớn nhất)')
async def statistic(column: str,  db: Session = Depends(get_db)):
    Book_list = get_data(db)
    Book_list = pd.DataFrame(Book_list)
    if column not in Book_list.columns:
        raise HTTPException(status_code=404, detail='Không tìm thấy tên cột trong dữ liệu')
    return calculate_statistics(Book_list, column)

# get - numpy
@app.get('/books/GetNumberBooks/{name_book}', status_code=200, description = "Trả về số sách của một cuốn sách còn trong shop (Đầu vào: String, tên cuốn sách - Đầu ra: int, số lượng sách còn trong cửa hàng)" )
def get_num_book(name_book:str,   db: Session = Depends(get_db)):
    Book_list = get_data(db)
    Book_list = pd.DataFrame(Book_list)
    lowercase_name_book = name_book.lower()  # Chuyển đổi tên cuốn sách thành chữ thường
    filtered_df = Book_list[Book_list['Namebook'].str.lower() == lowercase_name_book]
    if filtered_df.empty:
            raise HTTPException(status_code= 404, detail="Cuốn sách không có trong cửa hàng.")
    # Tính tổng số lượng sách còn trong cửa hàng
    num_books = np.sum(filtered_df['Quantity'])
    result = {
        'Tên Sách': name_book,
        'Số lượng sách': num_books
    }
    return result


# post - pandas
@app.post("/books/column_chart/{column_name}-{kind_chart}", status_code=201, description= "Trả về Biểu đồ của một Cột dữ liệu mà người dùng muốn vẽ (Đầu vào: String, tên cột và kiểu biểu đồ - Đầu ra: Biểu đồ dựa trên cột)")
async def column_chart(column_name: str, kind_chart : str,  db: Session = Depends(get_db)):
    Book_list = get_data(db)
    Book_list = pd.DataFrame(Book_list)
    if(column_name not in Book_list.columns):
        raise HTTPException(status_code = 404, detail = "Cột không tồn tại trong dữ liệu")
    try: 
        Book_list[column_name].value_counts().plot(kind= kind_chart)
        plt.savefig('chart.png')
        return FileResponse('chart.png', media_type='image/png')
    except:
        raise HTTPException(status_code= 400, detail="Loại biểu đồ không phù hợp với kiểu dữ liệu của cột")


# get - numpy 
@app.get("/books/sell_book_max", status_code= 200, description= "Trả về quyển sách được có lượt bán nhiều nhất shop (Đầu vào: None - Đầu ra: Quyển sách bán chạy nhất shop)")
async def sell_book_max(db: Session = Depends(get_db)):
    Book_list = get_data(db)
    Book_list = pd.DataFrame(Book_list)
    max_sold_books = np.where(Book_list['Sell'].values == np.max(Book_list['Sell'].values))
    max_sold_books = Book_list.iloc[max_sold_books]
    return max_sold_books.to_dict('records')

# post - numpy 
@app.post("/books/bookoutofsock", status_code= 200, description= "Thông báo cho người dùng những quyển sách đã hết hàng (Đầu vào: None - Đầu ra: Danh sách các cuốn sách đã hết hàng trong shop)")
async def book_out_of_stock(db: Session = Depends(get_db)):
    Book_list = get_data(db)
    Book_list = pd.DataFrame(Book_list)
    Book_out_of_stock = Book_list.loc[np.where(Book_list['Quantity'].values == 0)]
    book_out_of_stock_dict = Book_out_of_stock.to_dict(orient='records')
    return book_out_of_stock_dict
