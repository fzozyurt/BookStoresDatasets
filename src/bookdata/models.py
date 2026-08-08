"""Alan modelleri: kategori ve ürün (standart şema)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Category(BaseModel):
    name: str
    url: str
    parent: str | None = None


class Product(BaseModel):
    """Her iki sitede de ortak olan standart veri şeması."""

    title: str
    author: str = ""
    publisher: str = ""
    category: str
    price: float = Field(ge=0)
    url: str
    store: str
    scraped_at: datetime
    image_url: str | None = None
    isbn: str = ""
    currency: str = "TRY"
    availability: str = ""

    @property
    def csv_columns(self) -> list[str]:
        return [
            "Kitap İsmi",
            "Yazar",
            "Yayınevi",
            "Kategori",
            "Fiyat",
            "URL",
            "Site",
            "Tarih",
            "Resim",
            "ISBN",
            "Para Birimi",
            "Stok Durumu",
        ]

    def to_csv_row(self) -> list[str | int | float]:
        return [
            self.title,
            self.author,
            self.publisher,
            self.category,
            self.price,
            self.url,
            self.store,
            self.scraped_at.strftime("%Y-%m-%d %H:%M:%S"),
            self.image_url or "",
            self.isbn,
            self.currency,
            self.availability,
        ]
