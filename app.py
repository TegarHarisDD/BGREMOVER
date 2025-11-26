import streamlit as st
import numpy as np
from PIL import Image
import io
import os
import tempfile

# Try to import rembg, if not available, show installation instructions
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

def main():
    st.set_page_config(
        page_title="Background Remover",
        page_icon="🖼️",
        layout="wide"
    )
    
    st.title("🖼️ Background Remover App")
    st.markdown("Upload an image to remove its background automatically")
    
    # Check if rembg is available
    if not REMBG_AVAILABLE:
        st.error("""
        **rembg library is not installed!**
        
        To use this app, please install the required dependencies:
        ```bash
        pip install rembg streamlit Pillow
        ```
        
        You may also need to install additional dependencies for rembg:
        ```bash
        pip install rembg[gpu]  # for GPU support
        ```
        """)
        return
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("Instructions")
        st.markdown("""
        1. Upload an image (PNG, JPG, JPEG)
        2. Wait for processing
        3. Download the result
        4. Supported formats: PNG, JPG, JPEG
        
        **Note:** First run may take longer as models are downloaded.
        """)
        
        st.header("About")
        st.markdown("""
        This app uses AI to remove backgrounds from images.
        Powered by:
        - [rembg](https://github.com/danielgatis/rembg)
        - [Streamlit](https://streamlit.io)
        """)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['png', 'jpg', 'jpeg'],
        help="Upload an image to remove its background"
    )
    
    if uploaded_file is not None:
        # Display original image
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Image")
            original_image = Image.open(uploaded_file)
            st.image(original_image, use_column_width=True)
            
            # File info
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB",
                "Dimensions": f"{original_image.size[0]} x {original_image.size[1]}"
            }
            st.write(file_details)
        
        with col2:
            st.subheader("Processed Image")
            
            # Process the image
            with st.spinner("Removing background..."):
                try:
                    # Convert to RGB if necessary
                    if original_image.mode != 'RGB':
                        original_image = original_image.convert('RGB')
                    
                    # Remove background
                    processed_image = remove(original_image)
                    
                    # Display processed image
                    st.image(processed_image, use_column_width=True)
                    
                    # Download button
                    buf = io.BytesIO()
                    processed_image.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.download_button(
                        label="📥 Download Processed Image",
                        data=byte_im,
                        file_name=f"no_bg_{uploaded_file.name.split('.')[0]}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
                    st.info("Try uploading a different image or check the file format")

if __name__ == "__main__":
    main()
