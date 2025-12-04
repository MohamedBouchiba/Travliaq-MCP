"""
Translation tool for Travliaq MCP Server
Calls Travliaq-Translate service (NLLB-200 model)
"""
import httpx
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# URL du service de traduction (production)
TRANSLATE_SERVICE_URL = "https://travliaq-transalte-production.up.railway.app"


async def translate_text(
    text: str,
    source_language: str = "EN",
    target_language: str = "FR"
) -> Dict[str, Any]:
    """
    Traduit un texte d'une langue source vers une langue cible.
    
    Utilise le service Travliaq-Translate basé sur NLLB-200 (200 langues).
    
    Args:
        text: Texte à traduire (max 512 tokens)
        source_language: Code langue source (EN, FR, ES, DE, IT, PT, NL, RU, AR, ZH)
        target_language: Code langue cible (mêmes codes)
        
    Returns:
        Dict avec structure stable:
        - Succès: {"success": true, "translated_text": "...", "target_language": "fra_Latn"}
        - Erreur: {"success": false, "error": "..."}
        
    Examples:
        >>> await translate_text("Hello world", "EN", "FR")
        {"success": true, "translated_text": "Bonjour le monde", "target_language": "fra_Latn"}
        
        >>> await translate_text("Bienvenue à Paris", "FR", "ES")
        {"success": true, "translated_text": "Bienvenido a París", "target_language": "spa_Latn"}
    """
    if not text or not text.strip():
        return {
            "success": False,
            "error": "Text to translate cannot be empty"
        }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.debug(f"Translating: '{text[:50]}...' ({source_language} → {target_language})")
            
            response = await client.post(
                f"{TRANSLATE_SERVICE_URL}/translate",
                json={
                    "text": text,
                    "source_language": source_language,
                    "target_language": target_language
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✅ Translation successful: {source_language} → {target_language}")
            
            return {
                "success": True,
                "translated_text": result.get("translated_text", ""),
                "target_language": result.get("target_language", target_language)
            }
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            logger.error(f"❌ Translation HTTP error: {e.response.status_code} - {error_detail}")
            
            return {
                "success": False,
                "error": f"Translation service returned error {e.response.status_code}: {error_detail}"
            }
            
        except httpx.RequestError as e:
            logger.error(f"❌ Translation service unreachable: {str(e)}")
            
            return {
                "success": False,
                "error": f"Translation service unavailable: {str(e)}"
            }
            
        except Exception as e:
            logger.error(f"❌ Unexpected translation error: {str(e)}")
            
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }


async def translate_en(text: str) -> str:
    """
    Version ultra-simplifiée: Français → Anglais uniquement.
    
    Retourne directement le texte traduit (string), pas de dict.
    Parfait pour les agents qui veulent juste traduire sans se soucier du reste.
    
    Args:
        text: Texte en français à traduire
        
    Returns:
        Texte traduit en anglais (string simple)
        
    Examples:
        >>> await translate_en("Bonjour le monde")
        "Hello world"
        
        >>> await translate_en("N'oubliez pas d'acheter des souvenirs")
        "Don't forget to buy souvenirs"
    """
    result = await translate_text(text, source_language="FR", target_language="EN")
    
    if result.get("success"):
        return result["translated_text"]
    else:
        # En cas d'erreur, retourner le texte original
        logger.warning(f"Translation failed, returning original text: {result.get('error')}")
        return text

