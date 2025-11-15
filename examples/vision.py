"""Vision (image input) examples for the Devorbit SDK.

This example demonstrates how to use image inputs with different providers.
"""

import base64
import os
from pathlib import Path

from devorbit import Devorbit


def encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """Encode an image file to base64.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (base64_data, media_type)
    """
    path = Path(image_path)

    # Determine media type from extension
    extension = path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(extension, "image/jpeg")

    # Read and encode the image
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    return image_data, media_type


def example_image_from_base64():
    """Example using base64-encoded image."""
    print("\n=== Image from Base64 Example ===")

    # Note: You need to provide an actual image path
    # image_path = "path/to/your/image.jpg"
    # image_data, media_type = encode_image_to_base64(image_path)

    # For demonstration, we'll show the structure
    image_data = "..."  # Your base64 image data here
    media_type = "image/jpeg"

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                ],
            }
        ],
    )

    print(f"Response: {message.content[0].text}")


def example_image_from_url():
    """Example using image URL."""
    print("\n=== Image from URL Example ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # Use a public image URL
    image_url = (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg"
    )

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in detail."},
                    {
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": image_url,
                            "media_type": "image/jpeg",
                        },
                    },
                ],
            }
        ],
    )

    print(f"Response: {message.content[0].text}")


def example_multiple_images():
    """Example with multiple images."""
    print("\n=== Multiple Images Example ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # Example with two image URLs
    image_url_1 = "https://example.com/image1.jpg"
    image_url_2 = "https://example.com/image2.jpg"

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Compare these two images. What are the differences?"},
                    {
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": image_url_1,
                            "media_type": "image/jpeg",
                        },
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": image_url_2,
                            "media_type": "image/jpeg",
                        },
                    },
                ],
            }
        ],
    )

    print(f"Response: {message.content[0].text}")


def example_vision_with_openai():
    """Example of vision with OpenAI provider."""
    print("\n=== Vision with OpenAI ===")

    client = Devorbit(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

    message = client.messages.create(
        model="gpt-4-vision-preview",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": image_url,
                            "media_type": "image/jpeg",
                        },
                    },
                ],
            }
        ],
    )

    print(f"Response: {message.content[0].text}")


def example_vision_with_conversation():
    """Example of vision in a multi-turn conversation."""
    print("\n=== Vision in Conversation ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    image_url = "https://example.com/diagram.png"

    # First turn - describe the image
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this diagram?"},
                {
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": image_url,
                        "media_type": "image/png",
                    },
                },
            ],
        }
    ]

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=messages,
    )

    print(f"First response: {response.content[0].text}")

    # Second turn - follow-up question
    messages.append({"role": "assistant", "content": response.content[0].text})
    messages.append(
        {"role": "user", "content": "Can you explain the red component in more detail?"}
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=messages,
    )

    print(f"Follow-up response: {response.content[0].text}")


if __name__ == "__main__":
    print("Vision Examples")
    print("=" * 50)
    print("Note: These examples require valid image URLs or local image files.")
    print("Uncomment and modify the examples with your own images.")
    print("=" * 50)

    # Uncomment to run examples with actual images
    # example_image_from_url()
    # example_image_from_base64()
    # example_multiple_images()
    # example_vision_with_openai()
    # example_vision_with_conversation()

    print("\n=== Vision examples ready to use! ===")
    print("Please provide actual image URLs or paths to run the examples.")
