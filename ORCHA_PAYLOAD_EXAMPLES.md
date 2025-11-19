# Exemples de Payloads ORCHA JSON

Guide complet des formats de requêtes JSON pour l'API ORCHA avec support des images et du routing automatique vers Gemma.

---

## 📋 Table des Matières

1. [Image + Texte](#1-exemple-basique---image--texte)
2. [Avec MIME Type](#2-exemple-avec-mime-type)
3. [Multi-Images](#3-exemple-multi-images)
4. [Image Sans Texte](#4-exemple-image-sans-texte)
5. [Texte Seul](#5-exemple-texte-seul-sans-image)
6. [PDF + Image (Mixte)](#6-exemple-pdf--image-mixte)
7. [Avec RAG Activé](#7-exemple-avec-rag-activé)
8. [Nouvelle Conversation](#8-exemple-nouvelle-conversation)
9. [Avec Historique](#9-exemple-avec-historique)

---

## 1️⃣ Exemple Basique - Image + Texte

```json
{
  "user_id": 1,
  "tenant_id": "aura_tenant",
  "conversation_id": 42,
  "message": "Qu'est-ce que tu vois dans cette image ?",
  "attachments": [
    {
      "type": "image",
      "mime": "image/jpeg",
      "base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
      "filename": "photo.jpg"
    }
  ],
  "use_rag": false
}
```

### Ce qui se passe:
- ✅ Détection: `type == "image"` → **GEMMA MODEL**
- ✅ Route vers: `google/gemma-3-12b`
- ✅ Réponse: Analyse vision de l'image

### Logs Backend:
```
🎨 Routing to Gemma model in LM Studio with 1 image(s)
🎨 Model: google/gemma-3-12b
  📷 Image 1: photo.jpg (image/jpeg)
✅ Gemma response received
```

---

## 2️⃣ Exemple avec MIME Type

```json
{
  "user_id": 1,
  "message": "Analyse cette image",
  "attachments": [
    {
      "type": "file",
      "mime": "image/png",
      "base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
      "filename": "screenshot.png"
    }
  ]
}
```

### Ce qui se passe:
- ✅ Détection: `mime.startsWith("image/")` → **GEMMA MODEL**
- ✅ Route vers: `google/gemma-3-12b`
- ✅ Fonctionne même si `type != "image"`

---

## 3️⃣ Exemple Multi-Images

```json
{
  "user_id": 1,
  "conversation_id": 42,
  "message": "Compare ces deux images et dis-moi les différences",
  "attachments": [
    {
      "type": "image",
      "mime": "image/jpeg",
      "base64": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
      "filename": "image1.jpg"
    },
    {
      "type": "image",
      "mime": "image/png",
      "base64": "iVBORw0KGgoAAAANSUhEUgAAA...",
      "filename": "image2.png"
    },
    {
      "type": "image",
      "mime": "image/gif",
      "base64": "R0lGODlhAQABAIAAAAAAAP///...",
      "filename": "image3.gif"
    }
  ],
  "use_rag": false
}
```

### Ce qui se passe:
- ✅ Détection: 3 images → **GEMMA MODEL**
- ✅ Toutes les images envoyées à Gemma en une seule requête
- ✅ Réponse: Analyse comparative des images

### Réponse Attendue:
```json
{
  "status": "ok",
  "message": "En comparant ces trois images, je remarque que...",
  "vision_processed": true,
  "images_count": 3,
  "model_used": "google/gemma-3-12b",
  "image_filenames": ["image1.jpg", "image2.png", "image3.gif"]
}
```

---

## 4️⃣ Exemple Image Sans Texte

```json
{
  "user_id": 1,
  "message": "",
  "attachments": [
    {
      "type": "image",
      "base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
      "filename": "photo.jpg"
    }
  ]
}
```

### Ce qui se passe:
- ✅ Message vide détecté
- ✅ Backend ajoute automatiquement: `"User provided image; analyze it"`
- ✅ Route vers: **GEMMA MODEL**

### Note:
Le champ `mime` n'est pas obligatoire si `type == "image"`

---

## 5️⃣ Exemple Texte Seul (Sans Image)

```json
{
  "user_id": 1,
  "conversation_id": 42,
  "message": "Bonjour, comment ça va ?",
  "attachments": [],
  "use_rag": false
}
```

### Ce qui se passe:
- ✅ Aucune image détectée → **GPT-OSS20B (défaut)**
- ✅ Route vers: modèle texte normal
- ✅ Réponse: Chat texte standard

### Logs Backend:
```
📝 Routing to LM Studio (text-only) with 5 messages
```

---

## 6️⃣ Exemple PDF + Image (Mixte)

```json
{
  "user_id": 1,
  "message": "Analyse le document et l'image",
  "attachments": [
    {
      "type": "application/pdf",
      "base64": "JVBERi0xLjQKJeLjz9MKMSAwIG9ia...",
      "filename": "document.pdf"
    },
    {
      "type": "image",
      "mime": "image/jpeg",
      "base64": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
      "filename": "photo.jpg"
    }
  ],
  "use_rag": false
}
```

### Ce qui se passe:
- ✅ PDF: Texte extrait et ajouté au prompt
- ✅ Image: Détectée → Route vers **GEMMA MODEL**
- ✅ Réponse: Analyse combinée du document + image

### Réponse Attendue:
```json
{
  "status": "ok",
  "message": "D'après le document PDF et l'image fournie...",
  "attachments_processed": 2,
  "vision_processed": true,
  "images_count": 1,
  "pdf_text_length": 5432,
  "model_used": "google/gemma-3-12b"
}
```

---

## 7️⃣ Exemple avec RAG Activé

```json
{
  "user_id": 1,
  "conversation_id": 42,
  "message": "Basé sur mes documents, explique cette image",
  "attachments": [
    {
      "type": "image",
      "base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
      "filename": "chart.png"
    }
  ],
  "use_rag": true
}
```

### Ce qui se passe:
- ✅ RAG: Récupère contexte de la base de données vectorielle
- ✅ Image: Route vers **GEMMA MODEL**
- ✅ Contexte RAG ajouté au prompt système
- ✅ Réponse: Analyse avec contexte RAG + vision

### Réponse Attendue:
```json
{
  "status": "ok",
  "message": "En me basant sur vos documents précédents et l'analyse de cette image...",
  "contexts": [
    {
      "source": "document_123",
      "text": "Contexte pertinent du RAG...",
      "score": 0.95
    }
  ],
  "vision_processed": true,
  "images_count": 1
}
```

---

## 8️⃣ Exemple Nouvelle Conversation

```json
{
  "user_id": 1,
  "tenant_id": "aura_tenant",
  "message": "Analyse cette facture",
  "attachments": [
    {
      "type": "image",
      "mime": "image/jpeg",
      "base64": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
      "filename": "facture_2024.jpg"
    }
  ]
}
```

### Note:
- ❌ Pas de `conversation_id` fourni
- ✅ Nouvelle conversation créée automatiquement
- ✅ Le titre sera généré depuis le premier message

### Réponse Attendue:
```json
{
  "status": "ok",
  "message": "Cette facture montre...",
  "conversation_id": 123,  // ← Nouveau ID créé
  "vision_processed": true
}
```

---

## 9️⃣ Exemple avec Historique

```json
{
  "user_id": 1,
  "conversation_id": 42,
  "message": "Et maintenant regarde celle-ci",
  "attachments": [
    {
      "type": "image",
      "base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
      "filename": "image2.jpg"
    }
  ],
  "conversation_history": [
    {
      "role": "user",
      "content": "Analyse cette première image"
    },
    {
      "role": "assistant",
      "content": "Je vois un paysage avec un coucher de soleil..."
    }
  ]
}
```

### Ce qui se passe:
- ✅ Historique fourni par le frontend (optionnel)
- ✅ Si absent, chargé automatiquement depuis la base de données
- ✅ Image: Route vers **GEMMA MODEL**
- ✅ Continuité de la conversation avec contexte

---

## 📥 Réponses Attendues d'ORCHA

### Réponse avec Image (Vision Processing)

```json
{
  "status": "ok",
  "message": "Dans cette image, je peux voir un coucher de soleil sur l'océan avec des nuances d'orange et de rose dans le ciel. Les vagues sont calmes et on aperçoit des oiseaux au loin...",
  "conversation_id": 42,
  "contexts": [],
  "model_response": {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "model": "google/gemma-3-12b",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "Dans cette image, je peux voir..."
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 1234,
      "completion_tokens": 567,
      "total_tokens": 1801
    }
  },
  "token_usage": {
    "current_usage": 45678,
    "limit": 100000,
    "remaining": 54322,
    "reset_at": "2025-11-04T14:30:00Z"
  },
  "attachments_processed": 1,
  "vision_processed": true,
  "images_count": 1,
  "model_used": "google/gemma-3-12b",
  "image_filenames": ["photo.jpg"]
}
```

### Réponse sans Image (Texte Seul)

```json
{
  "status": "ok",
  "message": "Bonjour ! Je vais bien, merci. Comment puis-je vous aider aujourd'hui ?",
  "conversation_id": 42,
  "contexts": [],
  "model_response": {
    "id": "chatcmpl-456",
    "object": "chat.completion",
    "model": "gpt-oss20b",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "Bonjour ! Je vais bien..."
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 234,
      "completion_tokens": 89,
      "total_tokens": 323
    }
  },
  "token_usage": {
    "current_usage": 45355,
    "limit": 100000,
    "remaining": 54645,
    "reset_at": "2025-11-04T14:30:00Z"
  }
}
```

### Réponse en Cas d'Erreur

```json
{
  "status": "error",
  "error": "Image too large or invalid format",
  "error_type": "ValueError",
  "message": "Sorry, I encountered an error processing your request. Please try again.",
  "conversation_id": 42
}
```

---

## 🔍 Points Importants

### Format Base64

```javascript
// ✅ BON - Base64 pur (sans préfixe)
"base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA..."

// ✅ ACCEPTABLE - Avec préfixe (retiré automatiquement)
"base64": "data:image/jpeg;base64,iVBORw0KGg..."

// ❌ MAUVAIS - Format invalide
"base64": "C:\\Users\\photo.jpg"
```

**Note:** Le backend retire automatiquement le préfixe `data:image/*;base64,` si présent.

---

### Champs Requis et Optionnels

#### Minimum Requis:
```json
{
  "user_id": 1,
  "message": "...",
  "attachments": []
}
```

#### Payload Complet:
```json
{
  "user_id": 1,                    // REQUIS - ID utilisateur
  "tenant_id": "aura_tenant",      // OPTIONNEL - ID tenant/organisation
  "conversation_id": 42,           // OPTIONNEL - ID conversation (créé si absent)
  "message": "...",                // REQUIS - Texte (peut être vide si image présente)
  "attachments": [...],            // OPTIONNEL - Liste des pièces jointes
  "use_rag": false,               // OPTIONNEL - Activer RAG (défaut: false)
  "conversation_history": [...]   // OPTIONNEL - Historique (chargé depuis DB si absent)
}
```

---

### Structure d'un Attachment

#### Pour une Image:
```json
{
  "type": "image",              // "image" OU type MIME commençant par "image/"
  "mime": "image/jpeg",         // OPTIONNEL - Type MIME
  "base64": "...",              // REQUIS - Données base64
  "filename": "photo.jpg"       // OPTIONNEL - Nom du fichier
}
```

#### Pour un PDF:
```json
{
  "type": "application/pdf",
  "base64": "...",
  "filename": "document.pdf"
}
```

#### Avec URI (legacy):
```json
{
  "uri": "https://example.com/image.jpg",
  "type": "image/jpeg"
}
```

---

## 🎯 Règles de Routing

| Condition | Modèle Utilisé | Notes |
|-----------|----------------|-------|
| `attachment.type == "image"` | **Gemma** (`google/gemma-3-12b`) | Détection par type |
| `attachment.mime startsWith "image/"` | **Gemma** (`google/gemma-3-12b`) | Détection par MIME |
| Aucune image | **GPT-OSS20B** (défaut) | Chat texte standard |
| PDF + Image | **Gemma** | PDF extrait + vision |
| Multi-images | **Gemma** | Toutes images envoyées |

---

## 📊 Formats d'Images Supportés

- ✅ **JPEG** (`image/jpeg`, `.jpg`, `.jpeg`)
- ✅ **PNG** (`image/png`, `.png`)
- ✅ **GIF** (`image/gif`, `.gif`)
- ✅ **WebP** (`image/webp`, `.webp`)
- ✅ **BMP** (`image/bmp`, `.bmp`)

---

## ⚡ Exemples Rapides par Use Case

### Use Case 1: Analyse de Facture
```json
{
  "user_id": 1,
  "message": "Extrais les informations de cette facture",
  "attachments": [{"type": "image", "base64": "...", "filename": "facture.jpg"}]
}
```

### Use Case 2: Identification d'Objet
```json
{
  "user_id": 1,
  "message": "Qu'est-ce que c'est ?",
  "attachments": [{"type": "image", "base64": "...", "filename": "objet.png"}]
}
```

### Use Case 3: Transcription de Texte
```json
{
  "user_id": 1,
  "message": "Lis le texte dans cette image",
  "attachments": [{"type": "image", "base64": "...", "filename": "text.jpg"}]
}
```

### Use Case 4: Comparaison d'Images
```json
{
  "user_id": 1,
  "message": "Quelles sont les différences ?",
  "attachments": [
    {"type": "image", "base64": "...", "filename": "before.jpg"},
    {"type": "image", "base64": "...", "filename": "after.jpg"}
  ]
}
```

### Use Case 5: Chat Normal (Sans Image)
```json
{
  "user_id": 1,
  "message": "Explique-moi l'assurance santé"
}
```

---

## 🛠️ Testing avec cURL

### Test Image Simple
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "user_id": 1,
    "message": "Analyse cette image",
    "attachments": [{
      "type": "image",
      "base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
      "filename": "test.png"
    }]
  }'
```

### Test Texte Seul
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "user_id": 1,
    "message": "Bonjour, comment ça va ?"
  }'
```

---

## 📱 Intégration Frontend

Voir le fichier `FRONTEND_IMAGE_EXAMPLES.md` pour des exemples complets en JavaScript/React.

---

## 📝 Notes Techniques

### Taille Maximale Recommandée
- **Images:** ~5MB en base64 (~3.75MB original)
- **PDF:** ~10MB en base64 (~7.5MB original)

### Performance
- **Single image:** ~2-5 secondes
- **Multiple images:** ~5-10 secondes
- **Text only:** ~1-2 secondes

### Timeout
- Défaut: 500 secondes (configurable via `LM_TIMEOUT`)
- Augmenter si traitement de grandes images

---

## 🔗 Fichiers de Référence

- `IMAGE_ROUTING_GUIDE.md` - Guide complet de l'implémentation
- `FRONTEND_IMAGE_EXAMPLES.md` - Exemples frontend JavaScript/React
- `IMPLEMENTATION_COMPLETE.md` - Documentation technique complète
- `test_image_routing.py` - Tests unitaires

---

**Version:** 1.0.0  
**Dernière mise à jour:** 3 novembre 2025  
**Statut:** ✅ Production Ready















