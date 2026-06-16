import pdfplumber
import io
from fastapi import UploadFile

async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    ទាញយកអត្ថបទចេញពីឯកសារ PDF ដោយមិនចាំបាច់ Save ចូលកុំព្យូទ័រ។
    
    Args:
        file (UploadFile): ឯកសារ PDF ដែលទទួលបានពី FastAPI
        
    Returns:
        str: អត្ថបទដែលទាញយកបាន (ឬ String ទទេរ បើមាន Error)
    """
    try:
        # ១. អានទិន្នន័យ (Bytes) ពីឯកសារដែល Mobile App បោះមក
        file_bytes = await file.read()
        
        # ២. បង្កើត File-like Object នៅក្នុង RAM ដើម្បីឱ្យ pdfplumber អាចអានបាន
        pdf_file = io.BytesIO(file_bytes)
        
        extracted_text = ""
        
        # ៣. បើកអាន PDF ម្តងមួយទំព័រៗ រួចបូកអត្ថបទចូលគ្នា
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
                    
        # ៤. 🎯 ចំណុចសំខាន់បំផុត: ត្រឡប់ទស្សន៍ទ្រនិច (Cursor) ទៅដើមវិញ
        # បើមិនធ្វើបែបនេះទេ ពេលយក File នេះទៅ Upload ចូល Cloudinary វានឹងលោត Error ព្រោះ File ត្រូវអានដល់ចុងបាត់ហើយ។
        await file.seek(0)
        
        return extracted_text.strip()
        
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        # យើងរំកិល Cursor មកដើមវិញជានិច្ច ទោះបីជា Error ក៏ដោយ
        await file.seek(0) 
        return ""