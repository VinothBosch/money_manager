"""
Interactive setup script to configure the API key
"""

import os
from pathlib import Path

def setup_env_file():
    """Interactive setup for .env file"""
    print("\n" + "="*60)
    print("Bank Statement Processor - Setup Wizard")
    print("="*60)
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("\n.env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    print("\nChoose your AI provider:")
    print("1. OpenAI (Recommended)")
    print("2. Azure OpenAI")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n--- OpenAI Setup ---")
        print("Get your API key from: https://platform.openai.com/api-keys")
        api_key = input("\nEnter your OpenAI API key: ").strip()
        model = input("Enter model name (default: gpt-4): ").strip() or "gpt-4"
        
        env_content = f"""# OpenAI Configuration
OPENAI_API_KEY={api_key}
OPENAI_MODEL={model}

# Azure OpenAI Configuration (not used)
AZURE_OPENAI_DEPLOYMENT_NAME=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
"""
        
        # Update config.py
        config_update = "\nUSE_AZURE_OPENAI = False"
        
    elif choice == "2":
        print("\n--- Azure OpenAI Setup ---")
        deployment = input("Enter deployment name: ").strip()
        endpoint = input("Enter endpoint URL: ").strip()
        api_key = input("Enter API key: ").strip()
        
        env_content = f"""# Azure OpenAI Configuration
AZURE_OPENAI_DEPLOYMENT_NAME={deployment}
AZURE_OPENAI_ENDPOINT={endpoint}
AZURE_OPENAI_API_KEY={api_key}

# OpenAI Configuration (not used)
OPENAI_API_KEY=
OPENAI_MODEL=
"""
        
        config_update = "\nUSE_AZURE_OPENAI = True"
        
    else:
        print("Invalid choice. Setup cancelled.")
        return
    
    # Write .env file
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("\n[OK] .env file created successfully!")
    
    # Update config.py
    config_path = "money_manager/config.py"
    try:
        with open(config_path, "r") as f:
            config_content = f.read()
        
        # Update USE_AZURE_OPENAI setting
        if "USE_AZURE_OPENAI = True" in config_content or "USE_AZURE_OPENAI = False" in config_content:
            import re
            config_content = re.sub(
                r'USE_AZURE_OPENAI = (True|False)',
                f'USE_AZURE_OPENAI = {choice == "2"}',
                config_content
            )
            
            with open(config_path, "w") as f:
                f.write(config_content)
            
            print(f"[OK] {config_path} updated!")
    except Exception as e:
        print(f"[WARNING] Could not update {config_path}: {e}")
        print(f"Please manually set: USE_AZURE_OPENAI = {choice == '2'}")
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run: python tests/test_components.py")
    print("2. Run: python scripts/main.py")
    print("\n")

if __name__ == "__main__":
    try:
        setup_env_file()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
