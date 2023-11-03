"""
Author: Ali Binkowska
Date: September 2023
Description: class definitions for SERPAPI and Facebook data
"""

from pydantic import (
    BaseModel,
    constr,
    Field,
    parse_obj_as,
)
from typing import List, Optional, Tuple
from datetime import datetime


class GpsCoordinates(BaseModel):
    latitude: Optional[float] = 0
    longitude: Optional[float] = 0

class LocalResult(BaseModel):
    position: Optional[int] = 0
    title: Optional[str] = ""
    place_id: Optional[str] = ""
    data_id: Optional[str] = ""
    data_cid: Optional[str] = ""
    reviews_link: Optional[str] = ""
    photos_link: Optional[str] = ""
    gps_coordinates: GpsCoordinates
    place_id_search: Optional[str] = ""
    rating: Optional[float] = 0
    reviews: Optional[int] = 0
    price: Optional[str] = ""
    type: Optional[str] = ""
    types: List[Optional[str]] = Field(default_factory=list)
    address: Optional[str] = ""
    open_state: Optional[str] = ""
    hours: Optional[str] = ""
    operating_hours: Optional[dict] = Field(default_factory=dict)
    phone: Optional[str] = ""
    website: Optional[str] = ""
    service_options: Optional[dict] = Field(default_factory=dict)
    thumbnail: Optional[str] = ""
    processed: Optional[bool] = False
    has_lunch_menu: Optional[bool] = False
    # menu_frequency: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None



class FBPost(BaseModel):
    facebook_url: Optional[str] = Field(None, alias='facebookUrl')
    post_id: Optional[str] = Field(None, alias='postId')
    page_name: Optional[str] = Field(None, alias='pageName')
    url: Optional[str] = None
    time: Optional[datetime] = None
    timestamp: Optional[int] = None
    text: Optional[str] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    feedback_id: Optional[str] = Field(None, alias='feedbackId')
    top_level_url: Optional[str] = Field(None, alias='topLevelUrl')


    class Config:
        populate_by_name = True

class LocalWithFB(BaseModel):
    place_id: str
    facebook_url: str
    fb_post: Optional[FBPost] = None





