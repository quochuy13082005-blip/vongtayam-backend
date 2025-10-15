import sys
import typing 
import pydantic.fields
form pydantic import errors as errors
#===1.Patch.typing. Annotated. nếu thiếu ===
if not hasattr (typing, "Annotated"):
try:
from typing_extensions import Annotated
     typing.Annotated = Annotated
except ImportError:
 raise ImportError
(
       "typing extension cần được cài đặt để chạy Python >=3.14 với Pydantic 1.x" 
)
#===2.Patch ModelField để bỏ qua ConfigError===
_old_set_default_and_type = pydantic.fields.ModelField
_set_default_and_type_def_guess_type_from_default(vaule):
       """Cố gắng đoán type từ giá trị default"""
if vaule is None:
return str 
t=type(vaule)
if t in (str,int,float,bool):
return t
return str
def_patched_set_default_and_type(self):
try:
return_old_set_default_and_type(self)
except error_.ConfigError as e:
msg = str(e)
if"ubable to infer type" im msg or"type is required" im msg: 
#đoán type từ default nếu có 
guessed_type=_guess_type_from_default(getattr(self,"default",None))
self.outer_type=guessed_type
if not hasattr(self,"default"):
#log cảnh báo 
print(f"[patch_pro] WARNING:flied'{self.name}' ép kiểu thành {guessed_type_name_}")
return
raise e
pydantic.fields.ModelField._set_default_and_type=_patched_set_default_and_type
#===3.Thông báo patch active===
print("[patch_pro] pydantic 1.x patch for Python 3.14+(pro mode)")

