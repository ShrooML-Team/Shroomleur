#!/usr/bin/env python3
"""
Script de test complet pour l'API Shroomleur
Teste tous les endpoints : authentification, profils, historique, etc.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Couleurs pour l'affichage
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Variables globales pour les tests
access_token = None
registered_user_id = None
test_results = {"passed": 0, "failed": 0}


def print_header(title):
    """Afficher un en-tête de section"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{title:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")


def print_test(name):
    """Afficher le démarrage d'un test"""
    print(f"{BOLD}{YELLOW}→ {name}{RESET}")


def print_success(message):
    """Afficher un succès"""
    global test_results
    test_results["passed"] += 1
    print(f"  {GREEN}✓ {message}{RESET}")


def print_error(message):
    """Afficher une erreur"""
    global test_results
    test_results["failed"] += 1
    print(f"  {RED}✗ {message}{RESET}")


def print_info(message):
    """Afficher une info"""
    print(f"  {BLUE}ℹ {message}{RESET}")


def make_request(method, endpoint, data=None, token=None):
    """
    Faire une requête HTTP
    
    Args:
        method: GET, POST, PUT, DELETE
        endpoint: chemin de l'endpoint (ex: /auth/register)
        data: données à envoyer (dict)
        token: JWT token d'authentification
    
    Returns:
        (status_code, response_data)
    """
    url = f"{BASE_URL}{endpoint}"
    headers = HEADERS.copy()
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=5)
        else:
            return None, {"error": f"Méthode inconnue: {method}"}
        
        try:
            response_data = response.json()
        except:
            response_data = {"text": response.text}
        
        return response.status_code, response_data
    except requests.exceptions.RequestException as e:
        return None, {"error": str(e)}


# ============================================================================
# TESTS
# ============================================================================

def test_health_check():
    """Test 1 : Vérifier que l'API répond"""
    print_header("TEST 1 : Health Check")
    
    print_test("GET / (root)")
    status, data = make_request("GET", "/")
    if status == 200:
        print_success(f"API accessible (status: {status})")
        print_info(f"Message: {data.get('message', 'N/A')}")
    else:
        print_error(f"API inaccessible (status: {status})")
        return False
    
    print_test("GET /health")
    status, data = make_request("GET", "/health")
    if status == 200:
        print_success(f"Health check OK (status: {status})")
        print_info(f"Status: {data.get('status', 'N/A')}")
    else:
        print_error(f"Health check échoué (status: {status})")
        return False
    
    return True


def test_registration():
    """Test 2 : Inscription d'un nouvel utilisateur"""
    global access_token, registered_user_id
    
    print_header("TEST 2 : Inscription (POST /auth/register)")
    
    user_data = {
        "identifiant": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "mot_de_passe": "SecurePassword123!",
        "champignon_prefere": "Boletus edulis"
    }
    
    print_test(f"Inscription avec identifiant: {user_data['identifiant']}")
    status, data = make_request("POST", "/auth/register", data=user_data)
    
    if status == 200:
        print_success(f"Inscription réussie (status: {status})")
        
        # Vérifier les champs retournés
        if "access_token" in data:
            access_token = data["access_token"]
            print_success("Token JWT obtenu")
            print_info(f"Token: {access_token[:50]}...")
        else:
            print_error("Pas de token retourné")
            return False
        
        if "user" in data:
            user = data["user"]
            registered_user_id = user.get("id")
            print_success("Données utilisateur retournées")
            print_info(f"ID: {user.get('id')}")
            print_info(f"Email: {user.get('email')}")
            print_info(f"Identifiant: {user.get('identifiant')}")
            print_info(f"Scoring: {user.get('scoring')}")
            print_info(f"Niveau: {user.get('niveau')}")
            print_info(f"Streak: {user.get('streak')}")
        else:
            print_error("Pas de données utilisateur")
            return False
    else:
        print_error(f"Inscription échouée (status: {status})")
        print_info(f"Réponse: {json.dumps(data, indent=2)}")
        return False
    
    return True


def test_login():
    """Test 3 : Connexion avec identifiant et mot de passe"""
    print_header("TEST 3 : Connexion (POST /auth/login)")
    
    credentials = {
        "identifiant": "testuser_1709394000",  # À adapter avec un identifiant existant
        "mot_de_passe": "SecurePassword123!"
    }
    
    print_test(f"Connexion avec identifiant: {credentials['identifiant']}")
    status, data = make_request("POST", "/auth/login", data=credentials)
    
    if status == 200:
        print_success(f"Connexion réussie (status: {status})")
        
        if "access_token" in data:
            print_success("Token JWT obtenu")
            print_info(f"Token: {data['access_token'][:50]}...")
        else:
            print_error("Pas de token retourné")
            return False
        
        if "user" in data:
            user = data["user"]
            print_success("Données utilisateur retournées")
            print_info(f"Email: {user.get('email')}")
        else:
            print_error("Pas de données utilisateur")
            return False
    else:
        print_error(f"Connexion échouée (status: {status})")
        print_info(f"Réponse: {json.dumps(data, indent=2)}")
        return False
    
    return True


def test_get_profile():
    """Test 4 : Récupérer le profil personnel"""
    print_header("TEST 4 : Récupérer le profil (GET /users/me)")
    
    if not access_token:
        print_error("Pas de token disponible - exécuter test_registration d'abord")
        return False
    
    print_test("Récupération du profil personnel")
    status, data = make_request("GET", "/users/me", token=access_token)
    
    if status == 200:
        print_success(f"Profil récupéré (status: {status})")
        print_info(f"ID: {data.get('id')}")
        print_info(f"Identifiant: {data.get('identifiant')}")
        print_info(f"Email: {data.get('email')}")
        print_info(f"Description: {data.get('description', 'Non définie')}")
        print_info(f"Champignon préféré: {data.get('champignon_prefere', 'Non défini')}")
        print_info(f"Scoring: {data.get('scoring')}")
        print_info(f"Niveau: {data.get('niveau')}")
        print_info(f"Streak: {data.get('streak')}")
        print_info(f"Créé à: {data.get('created_at')}")
    else:
        print_error(f"Erreur lors de la récupération du profil (status: {status})")
        print_info(f"Réponse: {json.dumps(data, indent=2)}")
        return False
    
    return True


def test_update_profile():
    """Test 5 : Modifier le profil"""
    print_header("TEST 5 : Modifier le profil (PUT /users/me)")
    
    if not access_token:
        print_error("Pas de token disponible - exécuter test_registration d'abord")
        return False
    
    update_data = {
        "description": "Je suis passionné par les champignons !",
        "champignon_prefere": "Amanita muscaria",
        "photo_profil": "https://example.com/photo.jpg"
    }
    
    print_test("Modification du profil")
    status, data = make_request("PUT", "/users/me", data=update_data, token=access_token)
    
    if status == 200:
        print_success(f"Profil modifié (status: {status})")
        print_info(f"Description: {data.get('description')}")
        print_info(f"Champignon préféré: {data.get('champignon_prefere')}")
        print_info(f"Photo profil: {data.get('photo_profil')}")
    else:
        print_error(f"Erreur lors de la modification (status: {status})")
        print_info(f"Réponse: {json.dumps(data, indent=2)}")
        return False
    
    return True


def test_get_public_profile():
    """Test 6 : Récupérer le profil public d'un utilisateur"""
    print_header("TEST 6 : Profil public (GET /users/{user_id})")
    
    if not registered_user_id:
        print_error("Pas d'ID utilisateur disponible")
        return False
    
    print_test(f"Récupération du profil public de l'utilisateur {registered_user_id}")
    status, data = make_request("GET", f"/users/{registered_user_id}")
    
    if status == 200:
        print_success(f"Profil public récupéré (status: {status})")
        print_info(f"Identifiant: {data.get('identifiant')}")
        print_info(f"Scoring: {data.get('scoring')}")
        print_info(f"Niveau: {data.get('niveau')}")
        print_info(f"Streak: {data.get('streak')}")
    else:
        print_error(f"Erreur lors de la récupération (status: {status})")
        print_info(f"Réponse: {json.dumps(data, indent=2)}")
        return False
    
    return True


def test_add_items():
    """Test 7 : Ajouter des items à l'inventaire"""
    print_header("TEST 7 : Ajouter des items (POST /users/me/items/{item_name})")
    
    if not access_token:
        print_error("Pas de token disponible")
        return False
    
    items = ["Panier", "Loupe", "Carnet"]
    
    for item in items:
        print_test(f"Ajout de l'item: {item}")
        status, data = make_request("POST", f"/users/me/items/{item}?quantity=1", token=access_token)
        
        if status == 200:
            print_success(f"Item ajouté (status: {status})")
            print_info(f"Item: {data.get('item_name')}, Quantité: {data.get('quantity')}")
        else:
            print_error(f"Erreur lors de l'ajout (status: {status})")
    
    return True


def test_get_items():
    """Test 8 : Récupérer l'inventaire"""
    print_header("TEST 8 : Récupérer l'inventaire (GET /users/me/items)")
    
    if not access_token:
        print_error("Pas de token disponible")
        return False
    
    print_test("Récupération de l'inventaire")
    status, data = make_request("GET", "/users/me/items", token=access_token)
    
    if status == 200:
        print_success(f"Inventaire récupéré (status: {status})")
        if isinstance(data, list):
            print_info(f"Nombre d'items: {len(data)}")
            for item in data:
                print_info(f"  - {item.get('item_name')}: {item.get('quantity')} (acquis: {item.get('acquired_at')})")
        else:
            print_info(f"Réponse: {json.dumps(data, indent=2)}")
    else:
        print_error(f"Erreur lors de la récupération (status: {status})")
        print_info(f"Réponse: {json.dumps(data, indent=2)}")
        return False
    
    return True


def test_add_identification():
    """Test 9 : Enregistrer une identification"""
    print_header("TEST 9 : Enregistrer une identification (POST /users/me/history)")
    
    if not access_token:
        print_error("Pas de token disponible")
        return False
    
    identifications = [
        {
            "champignon": "Boletus edulis",
            "score": 95.0,
            "heure": "14:30:00",
            "localisation": "Forêt de Fontainebleau",
            "latitude": 48.4,
            "longitude": 2.65,
            "notes": "Bel exemplaire trouvé lors d'une promenade"
        },
        {
            "champignon": "Amanita muscaria",
            "score": 75.5,
            "heure": "15:45:00",
            "localisation": "Bois de Vincennes",
            "latitude": 48.82,
            "longitude": 2.43,
            "notes": "Reconnaissable à ses points blancs"
        },
        {
            "champignon": "Chanterelle commune",
            "score": 88.0,
            "heure": "10:15:00",
            "localisation": "Forêt locale",
            "latitude": None,
            "longitude": None,
            "notes": ""
        }
    ]
    
    for ident in identifications:
        print_test(f"Enregistrement: {ident['champignon']} (score: {ident['score']})")
        status, data = make_request("POST", "/users/me/history", data=ident, token=access_token)
        
        if status == 200:
            print_success(f"Identification enregistrée (status: {status})")
            print_info(f"ID: {data.get('id')}, Score: {data.get('score')}, Date: {data.get('date')}")
        else:
            print_error(f"Erreur lors de l'enregistrement (status: {status})")
            print_info(f"Réponse: {json.dumps(data, indent=2)}")
    
    return True


def test_get_history():
    """Test 10 : Récupérer l'historique"""
    print_header("TEST 10 : Récupérer l'historique (GET /users/me/history)")
    
    if not access_token:
        print_error("Pas de token disponible")
        return False
    
    print_test("Récupération de l'historique (limit=10)")
    status, data = make_request("GET", "/users/me/history?skip=0&limit=10", token=access_token)
    
    if status == 200:
        print_success(f"Historique récupéré (status: {status})")
        if isinstance(data, list):
            print_info(f"Nombre d'entrées: {len(data)}")
            for entry in data[:3]:  # Afficher les 3 premières
                print_info(f"  - {entry.get('champignon')}: {entry.get('score')} pts (le {entry.get('date')})")
        else:
            print_info(f"Réponse: {json.dumps(data, indent=2)}")
    else:
        print_error(f"Erreur lors de la récupération (status: {status})")
        print_info(f"Réponse: {json.dumps(data, indent=2)}")
        return False
    
    return True


def test_get_stats():
    """Test 11 : Récupérer les statistiques"""
    print_header("TEST 11 : Récupérer les statistiques (GET /users/me/history/stats)")
    
    if not access_token:
        print_error("Pas de token disponible")
        return False
    
    print_test("Récupération des statistiques")
    status, data = make_request("GET", "/users/me/history/stats", token=access_token)
    
    if status == 200:
        print_success(f"Statistiques récupérées (status: {status})")
        print_info(f"Scoring total: {data.get('scoring_total')}")
        print_info(f"Streak actuel: {data.get('streak_actuel')}")
        print_info(f"Niveau: {data.get('niveau')}")
        print_info(f"Total d'identifications: {data.get('total_identifications')}")
        print_info(f"Dernière identification: {data.get('derniere_identification', 'Aucune')}")
    else:
        print_error(f"Erreur lors de la récupération (status: {status})")
        print_info(f"Réponse: {json.dumps(data, indent=2)}")
        return False
    
    return True


def test_refresh_token():
    """Test 12 : Rafraîchir le token"""
    print_header("TEST 12 : Rafraîchir le token (POST /auth/refresh)")
    
    if not access_token:
        print_error("Pas de token disponible")
        return False
    
    print_test("Rafraîchissement du token")
    status, data = make_request("POST", "/auth/refresh", token=access_token)
    
    if status == 200:
        print_success(f"Token rafraîchi (status: {status})")
        new_token = data.get("access_token")
        if new_token:
            print_success("Nouveau token généré")
            print_info(f"Nouveau token: {new_token[:50]}...")
        else:
            print_error("Pas de nouveau token")
    else:
        print_error(f"Erreur lors du rafraîchissement (status: {status})")
        print_info(f"Réponse: {json.dumps(data, indent=2)}")
        return False
    
    return True


def test_error_handling():
    """Test 13 : Gestion des erreurs"""
    print_header("TEST 13 : Gestion des erreurs")
    
    print_test("Tentative sans token (GET /users/me)")
    status, data = make_request("GET", "/users/me")
    if status in [401, 403]:
        print_success(f"Erreur 401/403 retournée correctement")
    else:
        print_error(f"Erreur non validée (status: {status})")
    
    print_test("Tentative avec token invalide (GET /users/me)")
    status, data = make_request("GET", "/users/me", token="invalid_token")
    if status in [401, 403]:
        print_success(f"Token invalide rejeté")
    else:
        print_error(f"Token invalide non rejeté (status: {status})")
    
    print_test("Récupération d'utilisateur inexistant (GET /users/99999)")
    status, data = make_request("GET", "/users/99999")
    if status == 404:
        print_success(f"Utilisateur inexistant correctement rejeté")
    else:
        print_error(f"Erreur 404 non retournée (status: {status})")
    
    return True


def main():
    """Fonction principale"""
    print(f"\n{BOLD}{BLUE}")
    print(" " * 60)
    print(" " * 15 + "🍄 SHROOMLEUR API - SUITE DE TESTS 🍄")
    print(" " * 60)
    print(f"{RESET}")
    
    print(f"{YELLOW}Base URL: {BASE_URL}{RESET}")
    print(f"{YELLOW}Heure de démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")
    
    try:
        # Exécuter les tests dans l'ordre
        test_health_check()
        test_registration()
        test_login()
        test_get_profile()
        test_update_profile()
        test_get_public_profile()
        test_add_items()
        test_get_items()
        test_add_identification()
        test_get_history()
        test_get_stats()
        test_refresh_token()
        test_error_handling()
        
    except KeyboardInterrupt:
        print(f"\n\n{RED}Tests interrompus par l'utilisateur{RESET}")
        return
    except Exception as e:
        print(f"\n\n{RED}Erreur inattendue: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return
    
    # Afficher le résumé
    print_header("RÉSUMÉ DES TESTS")
    total = test_results["passed"] + test_results["failed"]
    
    print(f"{BOLD}{GREEN}Tests réussis: {test_results['passed']}/{total}{RESET}")
    print(f"{BOLD}{RED}Tests échoués: {test_results['failed']}/{total}{RESET}")
    
    if test_results["failed"] == 0:
        print(f"\n{BOLD}{GREEN}✓ Tous les tests réussis ! L'API fonctionne correctement.{RESET}\n")
    else:
        print(f"\n{BOLD}{RED}✗ {test_results['failed']} test(s) échoué(s). Vérifiez les logs ci-dessus.{RESET}\n")


if __name__ == "__main__":
    main()
