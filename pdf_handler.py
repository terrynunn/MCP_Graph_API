import io
import tempfile
from pathlib import Path
import PyPDF2

class PDFHandler:
    """Handler for processing PDF documents."""
    
    def parse_pdf(self, pdf_data):
        """Parse text content from a PDF document.

        Args:
            pdf_data: Raw PDF data as bytes or a file path

        Returns:
            dict: A dictionary with the following keys:
                - ``text``: Extracted text content as a single string.
                - ``pages``: Number of pages in the PDF.
                - ``success``: ``True`` if extraction succeeded, ``False`` otherwise.
                - ``error`` (optional): Error message when ``success`` is ``False``.
        """
        if isinstance(pdf_data, str) and Path(pdf_data).exists():
            # Handle file path
            with open(pdf_data, 'rb') as f:
                return self._extract_text_from_pdf(f)
        elif isinstance(pdf_data, bytes):
            # Handle raw bytes
            return self._extract_text_from_pdf(io.BytesIO(pdf_data))
        else:
            raise ValueError("Invalid PDF data format. Expected file path or bytes.")
    
    def _extract_text_from_pdf(self, pdf_file):
        """Extract text content from a PDF file object.

        Args:
            pdf_file: A file object containing PDF data

        Returns:
            dict: A dictionary with the following keys:
                - ``text``: Extracted text content as a single string.
                - ``pages``: Number of pages in the PDF.
                - ``success``: ``True`` if extraction succeeded, ``False`` otherwise.
                - ``error`` (optional): Error message when ``success`` is ``False``.
        """
        text = ""
        
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(reader.pages)
            
            # Extract text from each page
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"
                
            return {
                "text": text,
                "pages": num_pages,
                "success": True
            }
        except Exception as e:
            return {
                "text": "",
                "pages": 0,
                "success": False,
                "error": str(e)
            }
    
    def get_pdf_metadata(self, pdf_data):
        """Extract metadata from a PDF document.
        
        Args:
            pdf_data: Raw PDF data as bytes or a file path
            
        Returns:
            Dictionary of PDF metadata
        """
        if isinstance(pdf_data, str) and Path(pdf_data).exists():
            # Handle file path
            with open(pdf_data, 'rb') as f:
                return self._extract_metadata(f)
        elif isinstance(pdf_data, bytes):
            # Handle raw bytes
            return self._extract_metadata(io.BytesIO(pdf_data))
        else:
            raise ValueError("Invalid PDF data format. Expected file path or bytes.")
    
    def _extract_metadata(self, pdf_file):
        """Extract metadata from a PDF file object.
        
        Args:
            pdf_file: A file object containing PDF data
            
        Returns:
            Dictionary of PDF metadata
        """
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            info = reader.metadata
            
            metadata = {
                "title": info.title,
                "author": info.author,
                "subject": info.subject,
                "creator": info.creator,
                "producer": info.producer,
                "creation_date": info.creation_date,
                "modification_date": info.modification_date,
                "pages": len(reader.pages),
                "success": True
            }
            
            # Remove None values
            return {k: v for k, v in metadata.items() if v is not None}
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 