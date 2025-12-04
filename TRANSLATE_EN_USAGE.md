# Outil translate_en - Usage Ultra-Simple

## 🎯 Objectif

Outil **ultra-simple** pour les agents : juste texte FR → texte EN, rien d'autre.

## ✅ Usage

```python
# Dans un agent CrewAI
result = await mcp_tools.call_tool(
    "translate_en",
    text="N'oubliez pas d'acheter des souvenirs de dernière minute"
)
# → "Don't forget to buy last-minute souvenirs"
```

**C'est tout !** Pas de `source_language`, pas de `target_language`, pas de dict compliqué.

## 📝 Exemples

```python
# Exemple 1: Titre
translate_en("Découvrez les temples cachés de Tokyo")
→ "Discover the hidden temples of Tokyo"

# Exemple 2: Description
translate_en("Commencez votre aventure tokyoïte par la visite du majestueux Senso-ji")
→ "Start your Tokyo adventure by visiting the majestic Senso-ji"

# Exemple 3: Conseil
translate_en("Arrivez tôt le matin pour éviter la foule")
→ "Arrive early in the morning to avoid the crowds"
```

## 🔄 Gestion Erreurs

Si le service de traduction échoue, l'outil retourne le **texte original** en français.

```python
# Service down
translate_en("Bonjour")
→ "Bonjour"  # Fallback gracieux
```

## 🆚 Différence avec text.translate

| Outil            | Usage                            | Retour                          | Langues           |
| ---------------- | -------------------------------- | ------------------------------- | ----------------- |
| `translate_en`   | **Simple** : juste le texte      | String directe                  | FR → EN seulement |
| `text.translate` | **Flexible** : + source + target | Dict {success, translated_text} | 200 langues       |

**Recommandation:**

- **Agents simples** → Utiliser `translate_en` (plus facile)
- **Cas avancés** → Utiliser `text.translate` (plus flexible)

## 🚀 Configuration

URL production: `https://travliaq-transalte-production.up.railway.app`  
_(déjà configuré)_

Timeout: 30 secondes

## 📊 Performance

- Texte court (< 50 mots): **200-500ms**
- Texte moyen (100-200 mots): **500ms-1s**
- Texte long (300-400 mots): **1-2s**
