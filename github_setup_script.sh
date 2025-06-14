#!/bin/bash
# =============================================================================
# PNP Bot - GitHub to Google Cloud Run Setup Script
# Configura el pipeline completo desde GitHub a Google Cloud Run
# =============================================================================

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuración
PROJECT_ID="pnptelevision"
SERVICE_NAME="pnp-bot"
REGION="us-central1"
GITHUB_REPO_OWNER="pnpbots"  # CAMBIA ESTO
GITHUB_REPO_NAME="bot-hibrido"        # CAMBIA ESTO
BOT_TOKEN="7553238178:AAG7Co0Ft5ADp7S3UYV7cYHgjkSvuyK9a40"
ADMIN_USER_ID="7940478393"

# Functions
print_step() {
    echo -e "${BLUE}===> $1${NC}"
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

# Verificar prerequisites
check_prerequisites() {
    print_step "Verificando prerequisites..."
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK no está instalado"
        echo "Instala desde: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        echo "Instala desde: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        print_error "Git no está instalado"
        exit 1
    fi
    
    print_success "Prerequisites verificados"
}

# Configurar Google Cloud Project
setup_gcloud_project() {
    print_step "Configurando Google Cloud Project..."
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    print_step "Habilitando APIs necesarias..."
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    gcloud services enable artifactregistry.googleapis.com
    
    print_success "Google Cloud Project configurado"
}

# Crear secrets
create_secrets() {
    print_step "Creando secrets para información sensible..."
    
    # Create bot token secret
    echo "$BOT_TOKEN" | gcloud secrets create bot-token --data-file=- || \
    echo "$BOT_TOKEN" | gcloud secrets versions add bot-token --data-file=-
    
    # Create admin user ID secret
    echo "$ADMIN_USER_ID" | gcloud secrets create admin-user-id --data-file=- || \
    echo "$ADMIN_USER_ID" | gcloud secrets versions add admin-user-id --data-file=-
    
    # Grant Cloud Run access to secrets
    gcloud secrets add-iam-policy-binding bot-token \
        --member="serviceAccount:$PROJECT_ID@appspot.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    
    gcloud secrets add-iam-policy-binding admin-user-id \
        --member="serviceAccount:$PROJECT_ID@appspot.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    
    print_success "Secrets creados y configurados"
}

# Conectar GitHub repository
setup_github_integration() {
    print_step "Configurando integración con GitHub..."
    
    print_warning "Para conectar GitHub, necesitas:"
    echo "1. Ir a Google Cloud Console"
    echo "2. Cloud Build > Triggers" 
    echo "3. Connect Repository"
    echo "4. Seleccionar GitHub y autorizar"
    echo "5. Seleccionar tu repositorio: $GITHUB_REPO_OWNER/$GITHUB_REPO_NAME"
    echo ""
    read -p "¿Has conectado el repositorio? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Conecta el repositorio antes de continuar"
        exit 1
    fi
    
    print_success "Repositorio GitHub conectado"
}

# Crear triggers de Cloud Build
create_build_triggers() {
    print_step "Creando triggers de Cloud Build..."
    
    # Main branch trigger (production)
    gcloud builds triggers create github \
        --repo-name="$GITHUB_REPO_NAME" \
        --repo-owner="$GITHUB_REPO_OWNER" \
        --branch-pattern="^main$" \
        --build-config="cloudbuild.yaml" \
        --name="pnp-bot-main-deploy" \
        --description="Deploy PNP Bot from main branch" || true
    
    # Pull request trigger (testing)
    gcloud builds triggers create github \
        --repo-name="$GITHUB_REPO_NAME" \
        --repo-owner="$GITHUB_REPO_OWNER" \
        --pull-request-pattern=".*" \
        --build-config="cloudbuild.yaml" \
        --name="pnp-bot-pr-test" \
        --description="Test PNP Bot on pull requests" || true
    
    # Tag trigger (releases)
    gcloud builds triggers create github \
        --repo-name="$GITHUB_REPO_NAME" \
        --repo-owner="$GITHUB_REPO_OWNER" \
        --tag-pattern="v.*" \
        --build-config="cloudbuild.yaml" \
        --name="pnp-bot-release" \
        --description="Deploy PNP Bot releases" || true
    
    print_success "Triggers de Cloud Build creados"
}

# Test build manual
test_manual_build() {
    print_step "Ejecutando build manual de prueba..."
    
    # Submit manual build
    gcloud builds submit \
        --config cloudbuild.yaml \
        --substitutions _DEPLOY_REGION=$REGION,_SERVICE_NAME=$SERVICE_NAME
    
    print_success "Build manual completado"
}

# Setup monitoring
setup_monitoring() {
    print_step "Configurando monitoreo básico..."
    
    # Create uptime check
    gcloud alpha monitoring uptime create \
        --display-name="PNP Bot Health Check" \
        --http-check-path="/health" \
        --monitored-resource-type="gce_instance" \
        --timeout=10s \
        --period=60s || true
    
    print_success "Monitoreo configurado"
}

# Generate GitHub Actions workflow (optional)
create_github_actions() {
    print_step "Creando workflow de GitHub Actions (opcional)..."
    
    mkdir -p .github/workflows
    
    cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy PNP Bot to Google Cloud Run

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PROJECT_ID: pnptelevision
  SERVICE_NAME: pnp-bot
  REGION: us-central1

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Setup Google Cloud CLI
      uses: google-github-actions/setup-gcloud@v1
      with:
        project_id: ${{ env.PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        export_default_credentials: true
        
    - name: Configure Docker for GCR
      run: gcloud auth configure-docker
      
    - name: Build and Push Docker image
      run: |
        docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA .
        docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA
        
    - name: Deploy to Cloud Run
      if: github.ref == 'refs/heads/main'
      run: |
        gcloud run deploy $SERVICE_NAME \
          --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA \
          --platform managed \
          --region $REGION \
          --allow-unauthenticated \
          --memory 1Gi \
          --cpu 1 \
          --max-instances 3
EOF

    print_success "GitHub Actions workflow creado"
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "=================================================================="
    echo "         PNP Bot - GitHub to Google Cloud Run Setup"
    echo "=================================================================="
    echo -e "${NC}"
    
    print_warning "IMPORTANTE: Asegúrate de actualizar las variables:"
    echo "- GITHUB_REPO_OWNER: $GITHUB_REPO_OWNER"
    echo "- GITHUB_REPO_NAME: $GITHUB_REPO_NAME"
    echo ""
    read -p "¿Continuar con el setup? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelado"
        exit 0
    fi
    
    # Execute setup steps
    check_prerequisites
    setup_gcloud_project
    create_secrets
    setup_github_integration
    create_build_triggers
    create_github_actions
    
    # Optional steps
    read -p "¿Ejecutar build de prueba? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_manual_build
    fi
    
    read -p "¿Configurar monitoreo? (y/N): " -n 1 -r  
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_monitoring
    fi
    
    # Final instructions
    echo ""
    echo -e "${GREEN}=================================================================="
    echo "                        🎉 SETUP COMPLETADO!"
    echo "=================================================================="
    echo -e "${NC}"
    echo ""
    echo "📋 Próximos pasos:"
    echo "1. Subir tu código a GitHub:"
    echo "   git add ."
    echo "   git commit -m \"Initial PNP Bot setup\""
    echo "   git push origin main"
    echo ""
    echo "2. El bot se desplegará automáticamente"
    echo "3. Monitorear en Cloud Build Console"
    echo "4. Verificar en Cloud Run Console"
    echo ""
    echo "🔗 Enlaces útiles:"
    echo "- Cloud Build: https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
    echo "- Cloud Run: https://console.cloud.google.com/run?project=$PROJECT_ID"
    echo "- Logs: gcloud run services logs tail $SERVICE_NAME --region=$REGION"
    echo ""
    print_success "¡Tu bot está listo para funcionar! 🤖"
}

# Execute main function
main "$@"
