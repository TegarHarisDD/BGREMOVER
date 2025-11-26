import streamlit as st
import numpy as np
from PIL import Image
import io
import os
import tempfile
import zipfile
from datetime import datetime

# Try to import rembg, if not available, show installation instructions
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

def process_single_image(image):
    """Process a single image to remove background"""
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Remove background
    processed_image = remove(image)
    return processed_image

def create_zip_file(processed_images, original_filenames):
    """Create a ZIP file containing all processed images"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, (processed_image, original_filename) in enumerate(zip(processed_images, original_filenames)):
            # Create filename
            name_without_ext = os.path.splitext(original_filename)[0]
            output_filename = f"no_bg_{name_without_ext}.png"
            
            # Convert image to bytes
            img_buffer = io.BytesIO()
            processed_image.save(img_buffer, format="PNG")
            
            # Add to zip
            zip_file.writestr(output_filename, img_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer

def main():
    st.set_page_config(
        page_title="Background Remover",
        page_icon="🖼️",
        layout="wide"
    )
    
    st.title("🖼️ Background Remover App")
    st.markdown("Upload single or multiple images to remove their backgrounds automatically")
    
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
        **Single Image:**
        1. Upload one image (PNG, JPG, JPEG)
        2. Wait for processing
        3. Download the result
        
        **Multiple Images:**
        1. Upload multiple images
        2. Wait for batch processing
        3. Download all results as ZIP
        
        **Supported formats:** PNG, JPG, JPEG
        
        **Note:** First run may take longer as models are downloaded.
        """)
        
        st.header("About")
        st.markdown("""
        This app uses AI to remove backgrounds from images.
        Powered by:
        - [rembg](https://github.com/danielgatis/rembg)
        - [Streamlit](https://streamlit.io)
        """)
    
    # Tabs for single vs batch processing
    tab1, tab2 = st.tabs(["📷 Single Image", "📚 Batch Processing"])
    
    with tab1:
        st.subheader("Process Single Image")
        
        # Single file uploader
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a single image to remove its background",
            key="single"
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
                        processed_image = process_single_image(original_image)
                        
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
    
    with tab2:
        st.subheader("Process Multiple Images")
        
        # Multiple file uploader
        uploaded_files = st.file_uploader(
            "Choose multiple image files",
            type=['png', 'jpg', 'jpeg'],
            help="Upload multiple images to remove their backgrounds",
            accept_multiple_files=True,
            key="batch"
        )
        
        if uploaded_files:
            st.success(f"📁 {len(uploaded_files)} image(s) selected for processing")
            
            # Display file list
            with st.expander("📋 View Selected Files"):
                for i, file in enumerate(uploaded_files):
                    st.write(f"{i+1}. {file.name} ({file.size / 1024:.1f} KB)")
            
            # Process button
            if st.button("🚀 Process All Images", type="primary", use_container_width=True):
                if len(uploaded_files) > 20:
                    st.warning("⚠️ Processing more than 20 images may take a while. Consider processing in smaller batches.")
                
                processed_images = []
                original_filenames = []
                failed_files = []
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        # Update progress
                        progress = (i + 1) / len(uploaded_files)
                        progress_bar.progress(progress)
                        status_text.text(f"🔄 Processing {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
                        
                        # Process image
                        original_image = Image.open(uploaded_file)
                        processed_image = process_single_image(original_image)
                        
                        processed_images.append(processed_image)
                        original_filenames.append(uploaded_file.name)
                        
                    except Exception as e:
                        st.error(f"❌ Failed to process {uploaded_file.name}: {str(e)}")
                        failed_files.append(uploaded_file.name)
                        # Add placeholder to maintain order
                        processed_images.append(None)
                        original_filenames.append(uploaded_file.name)
                
                # Remove failed files
                successful_images = []
                successful_filenames = []
                
                for img, filename in zip(processed_images, original_filenames):
                    if img is not None:
                        successful_images.append(img)
                        successful_filenames.append(filename)
                
                if successful_images:
                    status_text.text("✅ Processing complete!")
                    progress_bar.empty()
                    
                    st.success(f"✅ Successfully processed {len(successful_images)} out of {len(uploaded_files)} images")
                    
                    if failed_files:
                        st.warning(f"❌ Failed to process {len(failed_files)} images: {', '.join(failed_files)}")
                    
                    # Create and download ZIP
                    with st.spinner("📦 Creating download package..."):
                        zip_buffer = create_zip_file(successful_images, successful_filenames)
                    
                    # Download button
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label=f"📥 Download All ({len(successful_images)} images) as ZIP",
                        data=zip_buffer,
                        file_name=f"background_removed_{timestamp}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    
                    # Preview first few images
                    st.subheader("👀 Preview Processed Images")
                    preview_cols = st.columns(min(3, len(successful_images)))
                    
                    for idx, (img, filename) in enumerate(zip(successful_images[:6], successful_filenames[:6])):
                        col_idx = idx % 3
                        with preview_cols[col_idx]:
                            st.image(img, use_column_width=True)
                            st.caption(f"{filename}")
                    
                    if len(successful_images) > 6:
                        st.info(f"✨ And {len(successful_images) - 6} more images in the download...")
                
                else:
                    st.error("❌ No images were successfully processed. Please check your files and try again.")

if __name__ == "__main__":
    main()
