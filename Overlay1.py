import streamlit as st
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import tempfile
import rasterio
from rasterio.transform import Affine
from rasterio.enums import Resampling

# Function to load and display the image
def load_image(image_file):
    img = Image.open(image_file)
    return img

# Function to georeference the image using Rasterio
def georeference_image(img_path, points, real_coords):
    with rasterio.open(img_path) as src:
        src_points = np.array(points, dtype=np.float32)
        dst_points = np.array(real_coords, dtype=np.float32)

        transform_matrix, *_ = cv2.getAffineTransform(src_points[:3], dst_points[:3])
        
        transform = Affine(
            transform_matrix[0][0], transform_matrix[0][1], transform_matrix[0][2],
            transform_matrix[1][0], transform_matrix[1][1], transform_matrix[1][2]
        )

        output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.tif').name
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=src.height,
            width=src.width,
            count=src.count,
            dtype=src.dtypes[0],
            crs='EPSG:4326',
            transform=transform,
        ) as dst:
            for i in range(1, src.count + 1):
                dst.write(src.read(i, resampling=Resampling.nearest), i)
    
    return output_path

# Main Streamlit app
st.title("Jeppesen Chart Georeferencing Tool")
st.write("Upload a Jeppesen chart to overlay on Google Earth")

image_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

if image_file is not None:
    img = load_image(image_file)
    st.image(img, caption="Uploaded Chart", use_column_width=True)

    st.write("Select reference points on the chart manually.")

    # Set up the drawing canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fill color with transparency
        stroke_width=2,
        stroke_color="#FF0000",
        background_image=img,
        update_streamlit=True,
        height=img.height,
        width=img.width,
        drawing_mode="point",
        point_display_radius=3,
        key="canvas",
    )

    if canvas_result.json_data is not None:
        points = [
            (p["left"], p["top"]) for p in canvas_result.json_data["objects"]
        ]
        st.write(f"Selected Points: {points}")

        if len(points) >= 3:
            st.write("Enter the corresponding real-world coordinates.")
            
            # Example real-world coordinates
            real_coords = [(34.000, -118.000), (34.001, -118.001), (34.002, -118.002)]
            st.write(f"Using Real-world Coordinates: {real_coords}")

            st.write("Georeferencing the image...")
            # Save the uploaded file to a temporary location
            temp_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
            img.save(temp_image_path)
            
            geo_img_path = georeference_image(temp_image_path, points, real_coords)

            # Download the georeferenced image
            st.write("Download the georeferenced image file.")
            st.download_button(label="Download Georeferenced Image", data=open(geo_img_path, 'rb').read(), file_name="georeferenced_chart.tif")
        else:
            st.write("Please select at least 3 points to proceed.")
