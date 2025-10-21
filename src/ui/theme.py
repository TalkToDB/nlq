"""
Custom theme configuration for the application.
"""

from gradio import themes

def create_theme():
    """Create a custom theme with better fonts and styling."""
    
    theme = themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
        font=[
            themes.GoogleFont("Inter"),
            "ui-sans-serif",
            "system-ui",
            "sans-serif"
        ],
        font_mono=[
            themes.GoogleFont("JetBrains Mono"),
            "ui-monospace",
            "monospace"
        ],
    ).set(
        # Layout
        body_background_fill="*neutral_50",
        body_text_color="*neutral_800",
        
        # Buttons
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_hover="*primary_700",
        button_primary_text_color="white",
        button_secondary_background_fill="*neutral_100",
        button_secondary_background_fill_hover="*neutral_200",
        button_secondary_text_color="*neutral_700",
        
        # Inputs
        input_background_fill="white",
        input_border_color="*neutral_300",
        input_border_color_focus="*primary_500",
        input_border_width="1px",
        input_radius="8px",
        
        # Blocks
        block_background_fill="white",
        block_border_width="1px",
        block_border_color="*neutral_200",
        block_radius="12px",
        block_shadow="0 1px 3px 0 rgb(0 0 0 / 0.1)",
        
        # Panels
        panel_background_fill="*neutral_50",
        panel_border_width="0px",
        
        # Tables
        table_border_color="*neutral_200",
        table_row_focus="*primary_50",
    )
    
    return theme
