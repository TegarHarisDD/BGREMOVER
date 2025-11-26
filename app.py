import streamlit as st
import numpy as np
from PIL import Image
import io
import os
import tempfile
import zipfile
from datetime import datetime

# Try to import rembg with better error handling
try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
except ImportError as e:
    st.error(f"rembg import failed: {e}")
    REMBG_AVAILABLE = False
except Exception as e:
    st.error(f"Unexpected error: {e}")
    REMBG_AVAILABLE = False

# Initialize session state for models
if 'model_loaded' not in st.session_state:
    st.session_state.model_loaded = False
if 'session' not in st.session_state:
    st.session_state.session = None

def load_model():
    """Load the background removal model"""
    try:
        if not REMBG_AVAILABLE:
            return False
        
        if st.session_state.session is None:
            # Use u2net model (lighter than u2netp)
            st.session_state.session = new_session("u2net")
            st.session_state.model_loaded = True
        return True
    except Exception as e:
        st.error(f"Failed to load model: {e}")
        return False

def process_single_image(image):
    """Process a single image to remove background"""
    try:
        if not load_model():
            return None
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Remove background
        processed_image = remove(image, session=st.session_state.session)
        return processed_image
    except Exception as e:
        st.error(f"Processing error: {e}")
        return None

def create_zip_file(processed_images, original_filenames):
    """Create a ZIP file containing all processed images"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, (processed_image, original_filename) in enumerate(zip(processed_images, original_filenames)):
            try:
                # Create filename
                name_without_ext = os.path.splitext(original_filename)[0]
                output_filename = f"no_bg_{name_without_ext}.png"
                
                # Convert image to bytes
                img_buffer = io.BytesIO()
                processed_image.save(img_buffer, format="PNG")
                
                # Add to zip
                zip_file.writestr(output_filename, img_buffer.getvalue())
            except Exception as e:
                st.error(f"Error adding {original_filename} to ZIP: {e}")
                continue
    
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
        **Required dependencies are not installed!**
        
        This app requires the `rembg` library which may not be available in this environment.
        
        **For Local Development:**
        ```bash
        pip install rembg streamlit Pillow
        ```
        
        **For Streamlit Cloud:**
        - Make sure `requirements.txt` includes `rembg`
        - Deploy with the provided `requirements.txt`
        - First load may take time to download models
        """)
        
        # Show installation instructions
        with st.expander("📋 Detailed Installation Instructions"):
            st.markdown("""
            ### Local Installation
            ```bash
            # Create virtual environment (recommended)
            python -m venv bg_remover_env
            source bg_remover_env/bin/activate  # On Windows: bg_remover_env\\Scripts\\activate
            
            # Install dependencies
            pip install -r requirements.txt
            ```
            
            ### Streamlit Cloud Deployment
            1. Fork the repository on GitHub
            2. Go to [share.streamlit.io](https://share.streamlit.io)
            3. Connect your GitHub account
            4. Select repository and branch
            5. Set main file to `app.py`
            6. Deploy!
            
            **Note:** First deployment may take 5-10 minutes to install dependencies.
            """)
        return
    
    # Initialize model on first run
    if not st.session_state.model_loaded:
        with st.spinner("🔄 Loading AI model (first time may take a while)..."):
            if load_model():
                st.session_state.model_loaded = True
                st.success("✅ Model loaded successfully!")
            else:
                st.error("❌ Failed to load model. Please check the dependencies.")
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
        
        **Note:** Processing time depends on image size and complexity.
        """)
        
        st.header("About")
        st.markdown("""
        This app uses AI to remove backgrounds from images.
        Powered by:
        - [rembg](https://github.com/danielgatis/rembg)
        - [Streamlit](https://streamlit.io)
        """)
        
        # Model info
        st.header("Model Status")
        if st.session_state.model_loaded:
            st.success("✅ Model Ready")
        else:
            st.warning("⚠️ Loading Model...")
    
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
                try:
                    original_image = Image.open(uploaded_file)
                    st.image(original_image, use_column_width=True)
                    
                    # File info
                    file_details = {
                        "Filename": uploaded_file.name,
                        "File size": f"{uploaded_file.size / 1024:.2f} KB",
                        "Dimensions": f"{original_image.size[0]} x {original_image.size[1]}"
                    }
                    st.write(file_details)
                except Exception as e:
                    st.error(f"Error loading image: {e}")
                    st.stop()
            
            with col2:
                st.subheader("Processed Image")
                
                # Process the image
                with st.spinner("Removing background..."):
                    try:
                        processed_image = process_single_image(original_image)
                        
                        if processed_image is not None:
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
                        else:
                            st.error("Failed to process image. Please try again.")
                            
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
                if len(uploaded_files) > 10:
                    st.warning("⚠️ Processing more than 10 images may take a while. Consider processing in smaller batches.")
                
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
                        
                        if processed_image is not None:
                            processed_images.append(processed_image)
                            original_filenames.append(uploaded_file.name)
                        else:
                            failed_files.append(uploaded_file.name)
                            
                    except Exception as e:
                        st.error(f"❌ Failed to process {uploaded_file.name}: {str(e)}")
                        failed_files.append(uploaded_file.name)
                
                if processed_images:
                    status_text.text("✅ Processing complete!")
                    progress_bar.empty()
                    
                    st.success(f"✅ Successfully processed {len(processed_images)} out of {len(uploaded_files)} images")
                    
                    if failed_files:
                        st.warning(f"❌ Failed to process {len(failed_files)} images: {', '.join(failed_files)}")
                    
                    # Create and download ZIP
                    with st.spinner("📦 Creating download package..."):
                        zip_buffer = create_zip_file(processed_images, original_filenames)
                    
                    # Download button
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label=f"📥 Download All ({len(processed_images)} images) as ZIP",
                        data=zip_buffer,
                        file_name=f"background_removed_{timestamp}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    
                    # Preview first few images
                    st.subheader("👀 Preview Processed Images")
                    preview_cols = st.columns(min(3, len(processed_images)))
                    
                    for idx, (img, filename) in enumerate(zip(processed_images[:6], original_filenames[:6])):
                        col_idx = idx % 3
                        with preview_cols[col_idx]:
                            st.image(img, use_column_width=True)
                            st.caption(f"{filename}")
                    
                    if len(processed_images) > 6:
                        st.info(f"✨ And {len(processed_images) - 6} more images in the download...")
                
                else:
                    st.error("❌ No images were successfully processed. Please check your files and try again.")

if __name__ == "__main__":
    main()
