#!/usr/bin/env python3
"""
Script de test pour l'API Shroomleur en local
Teste les endpoints: auth, users, et identification history
"""

import requests
import json
import base64
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_123"
TEST_EMAIL = f"test_{datetime.now().timestamp()}@test.com"
TEST_PASSWORD = "TestPassword123!"

# Couleurs pour les logs
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_result(test_name: str, success: bool, message: str = ""):
    """Affiche le résultat d'un test"""
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if success else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} - {test_name}")
    if message:
        print(f"  {Colors.YELLOW}→ {message}{Colors.END}")

def debug_token(token: str):
    """Décode et affiche le payload JWT sans vérification de signature"""
    try:
        parts = token.split(".")
        payload_b64 = parts[1] + "==" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        print(f"  {Colors.YELLOW}→ JWT payload: {payload}{Colors.END}")
    except Exception as e:
        print(f"  {Colors.RED}→ Impossible de décoder le token: {e}{Colors.END}")


def test_health_check():
    """Test l'endpoint de santé"""
    print(f"\n{Colors.BLUE}=== Test Health Check ==={Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        success = response.status_code == 200
        print_result("Health check", success, f"Status: {response.status_code}")
        return success
    except Exception as e:
        print_result("Health check", False, str(e))
        return False

def test_register():
    """Test l'enregistrement d'un nouvel utilisateur"""
    print(f"\n{Colors.BLUE}=== Test Registration ==={Colors.END}")
    try:
        payload = {
            "identifiant": TEST_USER_ID,
            "email": TEST_EMAIL,
            "mot_de_passe": TEST_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            token = data.get("access_token")
            print_result("Registration", success, f"User created: {TEST_USER_ID}")
            print_result("Token generation", bool(token), "JWT token received")
            if token:
                debug_token(token)
            return token
        else:
            print_result("Registration", success, f"Status: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_result("Registration", False, str(e))
        return None

def test_login(token_from_register=None):
    """Test la connexion"""
    print(f"\n{Colors.BLUE}=== Test Login ==={Colors.END}")
    try:
        payload = {
            "identifiant": TEST_USER_ID,
            "mot_de_passe": TEST_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            token = data.get("access_token")
            print_result("Login", success, f"Logged in as: {TEST_USER_ID}")
            print_result("Token generation", bool(token), "JWT token received")
            return token
        else:
            print_result("Login", success, f"Status: {response.status_code} - {response.text}")
            return token_from_register
    except Exception as e:
        print_result("Login", False, str(e))
        return token_from_register

def test_get_profile(token: str):
    """Test la récupération du profil utilisateur"""
    print(f"\n{Colors.BLUE}=== Test Get User Profile ==={Colors.END}")
    if not token:
        print_result("Get profile", False, "No token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/users/me", headers=headers)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_result("Get profile", success, f"User: {data.get('identifiant')}")
            return True
        else:
            print_result("Get profile", success, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Get profile", False, str(e))
        return False

def test_update_profile(token: str):
    """Test la mise à jour du profil"""
    print(f"\n{Colors.BLUE}=== Test Update Profile ==={Colors.END}")
    if not token:
        print_result("Update profile", False, "No token available")
        return False
    
    try:
        payload = {
            "description": "Passionné de mycologie 🍄",
            "champignon_prefere": "Cepe",
            "photo_profil": "https://example.com/profile.jpg"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(f"{BASE_URL}/users/me", json=payload, headers=headers)
        success = response.status_code == 200
        
        if success:
            print_result("Update profile", success, "Profile updated successfully")
            return True
        else:
            print_result("Update profile", success, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Update profile", False, str(e))
        return False

def test_add_identification(token: str):
    """Test l'ajout d'une identification de champignon"""
    print(f"\n{Colors.BLUE}=== Test Add Identification ==={Colors.END}")
    if not token:
        print_result("Add identification", False, "No token available")
        return False
    
    try:
        payload = {
            "champignon": "Cepe",
            "score": 85,
            "heure": "14:30",
            "localisation": "Forêt de Fontainebleau",
            "latitude": 48.4048,
            "longitude": 2.6968,
            "notes": "Trouvé sous un chêne"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/users/me/history", json=payload, headers=headers)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_result("Add identification", success, f"Mushroom: {data.get('champignon')}")
            print_result("Score recorded", True, f"Score: {data.get('score')}/100")
            return True
        else:
            print_result("Add identification", success, f"Status: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_result("Add identification", False, str(e))
        return False

def test_get_stats(token: str):
    """Test la récupération des statistiques"""
    print(f"\n{Colors.BLUE}=== Test Get Statistics ==={Colors.END}")
    if not token:
        print_result("Get statistics", False, "No token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/users/me/history/stats", headers=headers)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_result("Get statistics", success, "Statistics retrieved")
            print_result("Total identifications", True, f"Nombre: {data.get('total_identifications', 0)}")
            print_result("Average score", True, f"Score moyen: {data.get('average_score', 0):.2f}")
            return True
        else:
            print_result("Get statistics", success, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Get statistics", False, str(e))
        return False

def main():
    """Fonction principale - exécute tous les tests"""
    print(f"{Colors.BLUE}╔════════════════════════════════════════════╗{Colors.END}")
    print(f"{Colors.BLUE}║     SHROOMLEUR API - TEST SUITE            ║{Colors.END}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════════╝{Colors.END}")
    
    # Vérifier la connexion
    if not test_health_check():
        print(f"\n{Colors.RED}❌ API non accessible sur {BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Assurez-vous que l'API est démarrée avec: python -m uvicorn app.main:app --reload{Colors.END}")
        return
    
    # Créer un nouvel utilisateur ou utiliser un existant
    print(f"\n{Colors.YELLOW}Description: Création d'un nouvel utilisateur de test{Colors.END}")
    token = test_register()
    
    # Si l'inscription échoue (utilisateur existe), se connecter
    if not token:
        token = test_login()
    else:
        # Vérifier la connexion avec le token d'inscription
        test_login(token)
    
    # Tests si on a un token
    if token:
        test_get_profile(token)
        test_update_profile(token)
        test_add_identification(token)
        
        # Ajouter plusieurs identifications pour tester les stats
        print(f"\n{Colors.YELLOW}Ajout d'une deuxième identification pour les tests de statistiques...{Colors.END}")
        test_add_identification(token)
        
        test_get_stats(token)
    
    # Résumé final
    print(f"\n{Colors.BLUE}╔════════════════════════════════════════════╗{Colors.END}")
    print(f"{Colors.BLUE}║     FIN DES TESTS                          ║{Colors.END}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════════╝{Colors.END}")

if __name__ == "__main__":
    main()
