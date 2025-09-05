"""
HTML Integration System for Live Orbital Ballet
Comprehensive system to integrate any HTML file into Streamlit applications
"""

import streamlit as st
import streamlit.components.v1 as components
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import base64
from urllib.parse import quote
import tempfile

class HTMLIntegrator:
    """
    Comprehensive HTML integration system for Streamlit applications.
    Can handle any HTML file with automatic resource processing and JavaScript integration.
    """
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.loaded_templates = {}
        
    def load_html_file(self, file_path: str) -> str:
        """
        Load HTML content from file path.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            HTML content as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            st.error(f"Error loading HTML file {file_path}: {str(e)}")
            return ""
    
    def load_html_from_string(self, html_content: str, template_name: str = "custom") -> str:
        """
        Load HTML content from string input.
        
        Args:
            html_content: Full HTML content as string
            template_name: Name to identify this template
            
        Returns:
            Processed HTML content
        """
        self.loaded_templates[template_name] = html_content
        return html_content
    
    def process_html_resources(self, html_content: str) -> str:
        """
        Process HTML content to handle external resources (CSS, JS, images).
        Converts relative paths and inlines resources when possible.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Processed HTML content
        """
        # Extract and process CSS files
        css_pattern = r'<link[^>]*href=["\']([^"\']+\.css)["\'][^>]*>'
        css_matches = re.findall(css_pattern, html_content)
        
        for css_file in css_matches:
            try:
                if os.path.exists(css_file):
                    with open(css_file, 'r') as f:
                        css_content = f.read()
                    # Replace link tag with inline style
                    link_pattern = f'<link[^>]*href=["\'][^"\']*{re.escape(os.path.basename(css_file))}["\'][^>]*>'
                    html_content = re.sub(link_pattern, f'<style>{css_content}</style>', html_content)
            except Exception as e:
                st.warning(f"Could not inline CSS file {css_file}: {str(e)}")
        
        # Process JavaScript files
        js_pattern = r'<script[^>]*src=["\']([^"\']+\.js)["\'][^>]*></script>'
        js_matches = re.findall(js_pattern, html_content)
        
        for js_file in js_matches:
            try:
                if os.path.exists(js_file):
                    with open(js_file, 'r') as f:
                        js_content = f.read()
                    # Replace script tag with inline script
                    script_pattern = f'<script[^>]*src=["\'][^"\']*{re.escape(os.path.basename(js_file))}["\'][^>]*></script>'
                    html_content = re.sub(script_pattern, f'<script>{js_content}</script>', html_content)
            except Exception as e:
                st.warning(f"Could not inline JS file {js_file}: {str(e)}")
        
        # Process images
        img_pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>'
        img_matches = re.findall(img_pattern, html_content)
        
        for img_src in img_matches:
            try:
                if os.path.exists(img_src) and not img_src.startswith(('http', 'data:', '//')):
                    # Convert to base64 data URL
                    with open(img_src, 'rb') as f:
                        img_data = f.read()
                    
                    # Determine MIME type
                    ext = os.path.splitext(img_src)[1].lower()
                    mime_types = {
                        '.png': 'image/png',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.gif': 'image/gif',
                        '.svg': 'image/svg+xml'
                    }
                    mime_type = mime_types.get(ext, 'image/png')
                    
                    # Create data URL
                    img_b64 = base64.b64encode(img_data).decode()
                    data_url = f"data:{mime_type};base64,{img_b64}"
                    
                    # Replace src attribute
                    html_content = html_content.replace(f'src="{img_src}"', f'src="{data_url}"')
                    html_content = html_content.replace(f"src='{img_src}'", f"src='{data_url}'")
            except Exception as e:
                st.warning(f"Could not process image {img_src}: {str(e)}")
        
        return html_content
    
    def add_streamlit_bridge(self, html_content: str) -> str:
        """
        Add JavaScript bridge to communicate between HTML and Streamlit.
        
        Args:
            html_content: HTML content
            
        Returns:
            HTML content with Streamlit bridge
        """
        bridge_js = """
        <script>
            // Streamlit Bridge for HTML Integration
            window.streamlitBridge = {
                // Send data to Streamlit
                sendToStreamlit: function(data) {
                    if (window.parent) {
                        window.parent.postMessage({
                            type: 'streamlit-data',
                            data: data
                        }, '*');
                    }
                },
                
                // Receive data from Streamlit
                onStreamlitData: function(callback) {
                    window.addEventListener('message', function(event) {
                        if (event.data && event.data.type === 'streamlit-update') {
                            callback(event.data.data);
                        }
                    });
                },
                
                // Update HTML elements with Streamlit data
                updateElement: function(elementId, data) {
                    const element = document.getElementById(elementId);
                    if (element) {
                        if (typeof data === 'object') {
                            // Update multiple attributes/properties
                            Object.keys(data).forEach(key => {
                                if (key === 'innerHTML') {
                                    element.innerHTML = data[key];
                                } else if (key === 'textContent') {
                                    element.textContent = data[key];
                                } else if (key === 'style') {
                                    Object.assign(element.style, data[key]);
                                } else {
                                    element.setAttribute(key, data[key]);
                                }
                            });
                        } else {
                            // Simple text update
                            element.textContent = data;
                        }
                    }
                },
                
                // Trigger events in HTML from Streamlit
                triggerEvent: function(elementId, eventType, eventData) {
                    const element = document.getElementById(elementId);
                    if (element) {
                        const event = new CustomEvent(eventType, { detail: eventData });
                        element.dispatchEvent(event);
                    }
                }
            };
            
            // Initialize bridge
            document.addEventListener('DOMContentLoaded', function() {
                console.log('Streamlit HTML Bridge initialized');
                
                // Auto-setup common event listeners
                document.querySelectorAll('[data-streamlit-event]').forEach(element => {
                    const eventType = element.getAttribute('data-streamlit-event') || 'click';
                    const eventData = element.getAttribute('data-streamlit-data') || '';
                    
                    element.addEventListener(eventType, function(e) {
                        let dataToSend = eventData;
                        try {
                            dataToSend = JSON.parse(eventData);
                        } catch (ex) {
                            // Use as string if not valid JSON
                        }
                        
                        window.streamlitBridge.sendToStreamlit({
                            event: eventType,
                            element: element.id || element.className,
                            data: dataToSend,
                            value: element.value || element.textContent
                        });
                    });
                });
            });
        </script>
        """
        
        # Insert bridge before closing body tag, or at the end if no body tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{bridge_js}</body>')
        else:
            html_content += bridge_js
        
        return html_content
    
    def render_html(self, 
                   html_content: str, 
                   height: int = 600, 
                   scrolling: bool = True,
                   key: Optional[str] = None,
                   data: Optional[Dict] = None) -> Any:
        """
        Render HTML content in Streamlit using components.
        
        Args:
            html_content: HTML content to render
            height: Height of the HTML component
            scrolling: Whether to allow scrolling
            key: Unique key for the component
            data: Data to pass to the HTML component
            
        Returns:
            Component return value
        """
        # Process the HTML content
        processed_html = self.process_html_resources(html_content)
        processed_html = self.add_streamlit_bridge(processed_html)
        
        # Inject data if provided
        if data:
            data_script = f"""
            <script>
                window.streamlitData = {json.dumps(data)};
                
                // Auto-update elements with data-streamlit-bind attribute
                document.addEventListener('DOMContentLoaded', function() {{
                    document.querySelectorAll('[data-streamlit-bind]').forEach(element => {{
                        const bindPath = element.getAttribute('data-streamlit-bind');
                        const value = bindPath.split('.').reduce((obj, key) => obj && obj[key], window.streamlitData);
                        if (value !== undefined) {{
                            if (element.tagName === 'INPUT') {{
                                element.value = value;
                            }} else {{
                                element.textContent = value;
                            }}
                        }}
                    }});
                }});
            </script>
            """
            processed_html = processed_html.replace('</head>', f'{data_script}</head>')
        
        # Render using Streamlit components
        return components.html(
            processed_html,
            height=height,
            scrolling=scrolling,
            key=key
        )
    
    def create_html_uploader(self) -> Optional[str]:
        """
        Create a file uploader for HTML files in Streamlit.
        
        Returns:
            HTML content if file uploaded, None otherwise
        """
        uploaded_file = st.file_uploader(
            "Upload HTML File",
            type=['html', 'htm'],
            help="Upload any HTML file to integrate into the application"
        )
        
        if uploaded_file is not None:
            # Read the uploaded file
            html_content = uploaded_file.read().decode('utf-8')
            
            # Save to templates directory
            file_path = self.templates_dir / uploaded_file.name
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            st.success(f"HTML file '{uploaded_file.name}' uploaded and saved!")
            return html_content
        
        return None
    
    def create_html_editor(self, initial_content: str = "", key: str = "html_editor") -> str:
        """
        Create an HTML code editor in Streamlit.
        
        Args:
            initial_content: Initial HTML content
            key: Unique key for the editor
            
        Returns:
            Edited HTML content
        """
        return st.text_area(
            "HTML Content",
            value=initial_content,
            height=300,
            help="Paste or edit your HTML content here",
            key=key
        )
    
    def list_available_templates(self) -> List[str]:
        """
        List all available HTML templates.
        
        Returns:
            List of template names
        """
        templates = []
        for file_path in self.templates_dir.glob("*.html"):
            templates.append(file_path.stem)
        return templates
    
    def get_template_preview(self, template_name: str) -> str:
        """
        Get a preview of an HTML template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Preview of the template (first 500 characters)
        """
        template_path = self.templates_dir / f"{template_name}.html"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content[:500] + "..." if len(content) > 500 else content
        return "Template not found"

def create_html_integration_demo():
    """
    Create a demo interface for HTML integration.
    """
    st.title("🌐 HTML Integration System")
    st.markdown("Integrate any HTML file into your Live Orbital Ballet application!")
    
    integrator = HTMLIntegrator()
    
    # Create tabs for different integration methods
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Upload HTML", "✏️ Edit HTML", "📋 Templates", "🔧 Advanced"])
    
    with tab1:
        st.subheader("Upload HTML File")
        html_content = integrator.create_html_uploader()
        
        if html_content:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("HTML Preview")
                with st.expander("View HTML Source"):
                    st.code(html_content[:1000], language='html')
            
            with col2:
                st.subheader("Rendered Output")
                height = st.slider("Component Height", 200, 1000, 600)
                integrator.render_html(html_content, height=height, key="uploaded_html")
    
    with tab2:
        st.subheader("HTML Editor")
        
        # Sample HTML templates
        sample_templates = {
            "Simple Dashboard": """
<!DOCTYPE html>
<html>
<head>
    <title>Custom Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f0f0f0; margin: 20px; }
        .dashboard { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: #007bff; color: white; border-radius: 5px; }
        button { background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h2>Custom Satellite Dashboard</h2>
        <div class="metric">Satellites: <span data-streamlit-bind="satellites">0</span></div>
        <div class="metric">Active: <span data-streamlit-bind="active">0</span></div>
        <button data-streamlit-event="click" data-streamlit-data='{"action": "refresh"}'>Refresh Data</button>
    </div>
</body>
</html>
            """,
            "Interactive Map": """
<!DOCTYPE html>
<html>
<head>
    <title>Interactive Map</title>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; }
        #map { height: 400px; background: #1a1a2e; position: relative; }
        .control-panel { position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.8); color: white; padding: 15px; border-radius: 5px; }
        .satellite-dot { position: absolute; width: 8px; height: 8px; background: #00ff00; border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div id="map">
        <div class="control-panel">
            <h4>Satellite Map</h4>
            <p>Tracked: <span data-streamlit-bind="count">0</span></p>
            <button data-streamlit-event="click" data-streamlit-data='{"action": "center_view"}'>Center View</button>
        </div>
        <div class="satellite-dot" style="top: 50%; left: 30%;"></div>
        <div class="satellite-dot" style="top: 60%; left: 70%;"></div>
    </div>
</body>
</html>
            """
        }
        
        selected_template = st.selectbox("Choose Template", ["Custom"] + list(sample_templates.keys()))
        
        if selected_template != "Custom":
            initial_html = sample_templates[selected_template]
        else:
            initial_html = ""
        
        html_content = integrator.create_html_editor(initial_html, key="html_editor_main")
        
        if html_content.strip():
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Configuration")
                height = st.slider("Height", 200, 1000, 500)
                
                # Data injection
                st.subheader("Data Injection")
                use_data = st.checkbox("Inject Sample Data")
                sample_data = {}
                
                if use_data:
                    sample_data = {
                        "satellites": 63,
                        "active": 45,
                        "count": 12,
                        "status": "Operational"
                    }
                    st.json(sample_data)
            
            with col2:
                st.subheader("Rendered Output")
                integrator.render_html(
                    html_content, 
                    height=height, 
                    key="custom_html",
                    data=sample_data if use_data else None
                )
    
    with tab3:
        st.subheader("Available Templates")
        templates = integrator.list_available_templates()
        
        if templates:
            selected = st.selectbox("Select Template", templates)
            
            if selected:
                preview = integrator.get_template_preview(selected)
                st.code(preview, language='html')
                
                if st.button("Load Template"):
                    template_path = integrator.templates_dir / f"{selected}.html"
                    content = integrator.load_html_file(str(template_path))
                    integrator.render_html(content, key=f"template_{selected}")
        else:
            st.info("No templates found. Upload some HTML files to get started!")
    
    with tab4:
        st.subheader("Advanced Integration")
        st.markdown("""
        ### Features Available:
        - **Automatic Resource Processing**: CSS, JS, and images are automatically inlined
        - **Streamlit Bridge**: JavaScript bridge for two-way communication
        - **Data Binding**: Use `data-streamlit-bind="path"` to bind data
        - **Event Handling**: Use `data-streamlit-event="click"` for interactions
        - **Custom Styling**: Full CSS and JavaScript support
        
        ### Data Binding Example:
        ```html
        <span data-streamlit-bind="satellites">0</span>
        ```
        
        ### Event Handling Example:
        ```html
        <button data-streamlit-event="click" data-streamlit-data='{"action": "refresh"}'>
            Refresh
        </button>
        ```
        """)

# Example usage functions
def integrate_html_into_app(app_file: str, html_content: str, position: str = "main"):
    """
    Integrate HTML content into existing Streamlit app.
    
    Args:
        app_file: Path to Streamlit app file
        html_content: HTML content to integrate
        position: Where to place the HTML ("main", "sidebar", "header")
    """
    integrator = HTMLIntegrator()
    
    if position == "main":
        st.subheader("Custom HTML Component")
        integrator.render_html(html_content, key="integrated_html")
    elif position == "sidebar":
        with st.sidebar:
            st.subheader("Custom Panel")
            integrator.render_html(html_content, height=400, key="sidebar_html")
    elif position == "header":
        integrator.render_html(html_content, height=150, key="header_html")

if __name__ == "__main__":
    create_html_integration_demo()