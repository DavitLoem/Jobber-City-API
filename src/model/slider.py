from pydantic import BaseModel, Field
from typing import Optional

class SliderRequest(BaseModel):
    # ចំណងជើងនៅលើ Slider (ឧទាហរណ៍៖ "See how you can find a job quickly!")
    title: str = Field(..., min_length=5, max_length=150)
    
    # អត្ថបទនៅលើប៊ូតុង (Default គឺ "Read more")
    button_text: str = Field("Read more", max_length=30)
    
    # លីង (Link) សម្រាប់ទៅកាន់ទំព័រផ្សេងទៀតនៅពេលគេចុចលើប៊ូតុង
    link_url: Optional[str] = Field(None, example="/promotion/job-tips")
    
    # លំដាប់នៃការបង្ហាញ (Slider ណាបង្ហាញមុន ឬក្រោយ)
    order: int = Field(0, ge=0)
    
    # ស្ថានភាពបើក ឬបិទ Slider
    is_active: bool = Field(True)


