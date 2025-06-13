#!/bin/bash
# PNP Subscription Bot - Installation Script
# This script sets up the bot environment automatically

set -e  # Exit on any error

echo "🤖 PNP Television Subscription Bot - Installation Script"
echo "========================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python 3.8+ is installed
check_python() {
    print_info "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    python_major=$(echo $python_version | cut -d. -f1)
    python_minor=$(echo $python_version | cut -d. -f2)
    
    if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 8 ]); then
        print_error "Python 3.8 or higher required. Found: $python_version"
        exit 1
    fi
    
    print_success "Python $python_version found"
}

# Check if pip is available
check_pip() {
    print_info "Checking pip..."
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        print_info "Install with: sudo apt-get install python3-pip (Ubuntu/Debian)"
        exit 1
    fi
    print_success "pip3 found"
}

# Install dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_warning "requirements.txt not found, installing manually..."
        pip3 install python-telegram-bot>=20.6
        print_success "Core dependencies installed"
    fi
}

# Create directory structure
create_directories() {
    print_info "Creating directory structure..."
    
    # Create bot directory if it doesn't exist
    mkdir -p bot
    mkdir -p data
    mkdir -p logs
    
    print_success "Directories created"
}

# Setup environment file
setup_environment() {
    print_info "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Environment file created from template"
            print_warning "Please edit .env file with your actual configuration"
        else
            # Create basic .env file
            cat > .env << EOF
# PNP Subscription Bot Configuration
# REQUIRED: Get this from @BotFather on Telegram
BOT_TOKEN=your_bot_token_here

# OPTIONAL: Your user ID for admin access
ADMIN_IDS=

# OPTIONAL: Channel configuration
CHANNEL_ID=@your_private_channel
CHANNEL_NAME=PNP Television

# PAYMENT LINKS: Configure with your payment processor
WEEK_PAYMENT_LINK=
MONTH_PAYMENT_LINK=
3MONTH_PAYMENT_LINK=
HALFYEAR_PAYMENT_LINK=
YEAR_PAYMENT_LINK=
LIFETIME_PAYMENT_LINK=
EOF
            print_success "Basic environment file created"
            print_warning "Please edit .env file with your actual configuration"
        fi
    else
        print_info ".env file already exists, skipping..."
    fi
}

# Make scripts executable
make_executable() {
    print_info "Making scripts executable..."
    
    if [ -f "run_simple_bot.py" ]; then
        chmod +x run_simple_bot.py
        print_success "run_simple_bot.py is now executable"
    fi
    
    if [ -f "install.sh" ]; then
        chmod +x install.sh
        print_success "install.sh is now executable"
    fi
}

# Test installation
test_installation() {
    print_info "Testing installation..."
    
    if [ -f "run_simple_bot.py" ]; then
        if python3 run_simple_bot.py --validate-only 2>/dev/null; then
            print_success "Installation test passed"
        else
            print_warning "Installation test failed - please check your configuration"
            print_info "Run 'python3 run_simple_bot.py --validate-only' for details"
        fi
    else
        print_warning "run_simple_bot.py not found, skipping test"
    fi
}

# Show next steps
show_next_steps() {
    echo ""
    echo "🎉 Installation complete!"
    echo "========================================"
    echo ""
    echo "📋 Next steps:"
    echo "1. Edit the .env file with your bot token:"
    echo "   nano .env"
    echo ""
    echo "2. Get your bot token from @BotFather on Telegram"
    echo ""
    echo "3. Test your configuration:"
    echo "   python3 run_simple_bot.py --validate-only"
    echo ""
    echo "4. Start the bot:"
    echo "   python3 run_simple_bot.py"
    echo ""
    echo "📖 For more information, check README.md"
    echo ""
    print_success "Happy botting! 🤖"
}

# Main installation process
main() {
    check_python
    check_pip
    create_directories
    install_dependencies
    setup_environment
    make_executable
    test_installation
    show_next_steps
}

# Run if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi