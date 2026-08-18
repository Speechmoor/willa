"""Language registry and UI strings.

All 12 official languages are declared here so the selector and every
downstream path is built for the full set. Adding a language is a data change.

STATUS values:
  native   UI strings written or reviewed by a human; model has real coverage.
  mt       UI strings machine-translated; NLLB-200 covers the language.
  none     No model coverage. Needs a human translator or an SA-specific model.
  nontext  Not a written language.

Coverage checked 2026-08-12. NLLB-200 covers 9 of the 11 written languages.
Tshivenda and isiNdebele appear in neither NLLB-200 nor Qwen3.
"""

from typing import Literal

Status = Literal["native", "mt", "none", "nontext"]

LANGUAGES: list[dict] = [
    {"code": "en",  "name": "English",    "endonym": "English",     "nllb": "eng_Latn", "status": "native"},
    {"code": "af",  "name": "Afrikaans",  "endonym": "Afrikaans",   "nllb": "afr_Latn", "status": "native"},
    {"code": "zu",  "name": "isiZulu",    "endonym": "isiZulu",     "nllb": "zul_Latn", "status": "mt"},
    {"code": "xh",  "name": "isiXhosa",   "endonym": "isiXhosa",    "nllb": "xho_Latn", "status": "mt"},
    {"code": "st",  "name": "Sesotho",    "endonym": "Sesotho",     "nllb": "sot_Latn", "status": "mt"},
    {"code": "nso", "name": "Sepedi",     "endonym": "Sepedi",      "nllb": "nso_Latn", "status": "mt"},
    {"code": "tn",  "name": "Setswana",   "endonym": "Setswana",    "nllb": "tsn_Latn", "status": "mt"},
    {"code": "ss",  "name": "siSwati",    "endonym": "siSwati",     "nllb": "ssw_Latn", "status": "mt"},
    {"code": "ts",  "name": "Xitsonga",   "endonym": "Xitsonga",    "nllb": "tso_Latn", "status": "mt"},
    {"code": "ve",  "name": "Tshivenda",  "endonym": "Tshivenḓa",   "nllb": None,       "status": "none"},
    {"code": "nr",  "name": "isiNdebele", "endonym": "isiNdebele",  "nllb": None,       "status": "none"},
    {"code": "sasl","name": "SA Sign Language", "endonym": "SASL",  "nllb": None,       "status": "nontext"},
]

BY_CODE = {lang["code"]: lang for lang in LANGUAGES}

# UI strings. Only languages with hand-written strings appear here;
# everything else falls back to English in the UI while the *document*
# pipeline still honours the selected language.
STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "app_title": "Willa",
        "tagline": "Help preparing a Small Claims Court letter of demand",
        "choose_language": "Choose your language",
        "local_badge": "Runs on this device. Nothing is sent anywhere.",
        "step_your_details": "Your details",
        "step_other_party": "The other party",
        "step_claim": "Your claim",
        "your_name": "First name",
        "your_surname": "Surname",
        "your_address": "Your address",
        "your_email": "Your email (optional)",
        "other_name": "Their name or business name",
        "other_surname": "Their surname (if a person)",
        "other_address": "Their address",
        "other_email": "Their email (if you know it)",
        "amount": "Amount claimed (Rand)",
        "claim_basis": "What happened?",
        "claim_basis_hint": "Explain in your own words. What was agreed, what went wrong, and what you are owed.",
        "agreement_date": "Date of the purchase or agreement",
        "agreement_date_hint": "When you paid, signed, or agreed. Leave blank if it does not apply.",
        "failure_date": "Date it went wrong",
        "failure_date_hint": "When the goods failed, the work was not done, or payment fell due.",
        "generate": "Prepare my letter",
        "generating": "Preparing your letter…",
        "review_title": "Check this before you use it",
        "review_hint": "Read every line. Correct anything that is wrong. You are responsible for what you send.",
        "download": "Download as text",
        "save_pdf": "Save as PDF",
        "print_footer": "Prepared with Willa. Willa is not a lawyer and this is not legal advice. Check every detail before you sign and send this letter.",
        "start_over": "Start over",
        "disclaimer": "Willa is not a lawyer and this is not legal advice. A Small Claims Court commissioner decides your case on its merits.",
        "notice_days": "The other party has 14 days from receiving this letter to pay or settle.",
        "sources_title": "Based on",
        "unsupported_title": "Not available in this language yet",
        "unsupported_body": "We have not found a translation model that handles this language well enough to be trusted with a legal document. Rather than give you a bad translation, we are being upfront. You can continue in English or Afrikaans.",
        "sasl_body": "South African Sign Language is a signed language with no written form, so a written letter cannot be produced in it. Video guidance is planned but not built yet.",
        "mt_banner": "This page was translated by a computer and has not been checked by a person. Tell us if something reads wrongly.",
        "delivery_title": "Prove you delivered it",
        "delivery_intro": "Before you can issue a summons, you must prove the other side received this letter. How will you deliver it?",
        "delivery_post": "By registered post",
        "delivery_post_hint": "The post office receipt is your proof.",
        "delivery_personal": "By hand, myself",
        "delivery_personal_hint": "You will need a sworn affidavit.",
        "delivery_other": "Some other way",
        "delivery_other_hint": "You will need a sworn affidavit explaining how.",
        "id_number": "Your ID or passport number",
        "delivery_date": "Date you delivered it",
        "delivery_time": "Time you delivered it",
        "recipient_name": "Name of the person who took the letter",
        "recipient_hint": "If it was a shop, the name of whoever accepted it.",
        "delivery_place": "Where you delivered it",
        "other_method": "How did you deliver it?",
        "make_affidavit": "Prepare the affidavit",
        "affidavit_title": "Affidavit (Form 5)",
        "affidavit_warning": "Do not sign this yet. It is only valid once you sign it in front of a Commissioner of Oaths.",
        "summons_title": "If they do not pay",
        "summons_intro": "After 14 days with no payment, you can take the next step. Willa can prepare what you need to write on Form 1 \u2014 the hard part is describing your claim briefly, and that is what this does.",
        "summons_not_a_summons": "This is not a summons. Only the clerk of the court can issue one. This is the sheet you write onto the official form.",
        "your_phone": "Your phone number",
        "other_phone": "Their phone number (if you know it)",
        "admitted_debt": "Do you owe them anything? (Rand)",
        "admitted_debt_hint": "Leave blank if not. If you do, it can be deducted from your claim.",
        "make_summons": "Prepare my Form 1 notes",
        "making_summons": "Preparing\u2026",
        "save_title": "Save your claim to come back to",
        "save_intro": "Willa keeps nothing. If you want to carry on later, save a file to your own device and load it back when you return.",
        "save_file": "Save my claim to a file",
        "load_file": "Load a saved claim",
        "save_pass": "Password (optional)",
        "save_pass_hint": "If anyone else uses this device, set a password. Willa cannot recover it if you forget it \u2014 the file would be lost.",
        "save_shared_warning": "Anyone who finds this file can read your claim unless you set a password.",
        "save_done": "Saved. Keep it somewhere only you can reach.",
        "load_pass_prompt": "This file has a password. Enter it to open the claim.",
        "load_wrong_pass": "That password did not open the file. Check it and try again.",
        "load_bad_file": "That does not look like a Willa file.",
        "load_done": "Claim loaded. Your details have been filled in again.",
        "task_title": "What do you need today?",
        "task_letter": "Write a letter of demand",
        "task_letter_hint": "Start here. This is the first step \u2014 you must send this before you can go to court.",
        "task_affidavit": "Prove I delivered my letter",
        "task_affidavit_hint": "You have already sent your letter and need the affidavit (Form 5).",
        "task_court": "Prepare for court",
        "task_court_hint": "The 14 days have passed and they have not paid. Prepare what you write on Form 1.",
        "task_resume": "Continue a saved claim",
        "task_resume_hint": "Load the file you saved last time.",
        "back_to_tasks": "Back",
        "your_details_for_affidavit": "The affidavit needs your details. Fill these in if they are not already there.",
        "court_needs_claim": "The court form needs your claim details, including what happened. Fill these in, then prepare your notes.",
        "brand_1": "Permanent",
        "brand_2": "Sovereign",
        "brand_3": "Equal",
        "hero_kicker": "A privacy-first legal assistant for the Small Claims Court",
        "point_1": "5.1 billion people are shut out of the legal protections they are owed.",
        "point_2": "South Africa is the most unequal country in the world.",
        "point_3": "Legal standing is a right, not an economic privilege.",
        "point_4": "We are starting where the friction is highest.",
        "intro_enter": "Tap the circle to begin",
        "intro_listen": "Listen",
        "intro_stop": "Stop",
        "intro_no_voice": "This device has no voice installed for your language, so Willa cannot read this aloud. The words are on the screen.",
        "explain_title": "What this letter says",
        "explain_note": "The letter is in English because that is the language South African courts use. This summary is in your language so you know what you are signing.",
        "explain_show_en": "Show this in English",
        "explain_unavailable": "Willa could not produce this summary in your language, and will not show you English instead without telling you.",
        "pending_title": "Coming shortly",
        "pending_body": "A translation model that handles this language is being added. It is not installed yet, and we would rather tell you that than hand you an English letter you did not ask for. English and Afrikaans work today.",
    },
    "af": {
        "app_title": "Willa",
        "tagline": "Hulp met die opstel van 'n brief van aanmaning vir die Klein Eisehof",
        "choose_language": "Kies jou taal",
        "local_badge": "Werk op hierdie toestel. Niks word enige plek heen gestuur nie.",
        "step_your_details": "Jou besonderhede",
        "step_other_party": "Die ander party",
        "step_claim": "Jou eis",
        "your_name": "Naam",
        "your_surname": "Van",
        "your_address": "Jou adres",
        "your_email": "Jou e-pos (opsioneel)",
        "other_name": "Hul naam of besigheidsnaam",
        "other_surname": "Hul van (indien 'n persoon)",
        "other_address": "Hul adres",
        "other_email": "Hul e-pos (indien bekend)",
        "amount": "Bedrag geëis (Rand)",
        "claim_basis": "Wat het gebeur?",
        "claim_basis_hint": "Verduidelik in jou eie woorde. Wat is ooreengekom, wat het verkeerd geloop, en wat word aan jou geskuld.",
        "agreement_date": "Datum van die aankoop of ooreenkoms",
        "agreement_date_hint": "Wanneer jy betaal, geteken of ooreengekom het. Los leeg indien nie van toepassing nie.",
        "failure_date": "Datum waarop dit verkeerd geloop het",
        "failure_date_hint": "Wanneer die goedere gefaal het, die werk nie gedoen is nie, of betaling opeisbaar geword het.",
        "generate": "Berei my brief voor",
        "generating": "Jou brief word voorberei…",
        "review_title": "Gaan dit na voordat jy dit gebruik",
        "review_hint": "Lees elke reël. Korrigeer enigiets wat verkeerd is. Jy is verantwoordelik vir wat jy stuur.",
        "download": "Laai af as teks",
        "save_pdf": "Stoor as PDF",
        "print_footer": "Opgestel met Willa. Willa is nie 'n prokureur nie en dit is nie regsadvies nie. Gaan elke besonderheid na voordat jy hierdie brief onderteken en stuur.",
        "start_over": "Begin oor",
        "disclaimer": "Willa is nie 'n prokureur nie en dit is nie regsadvies nie. 'n Kommissaris van die Klein Eisehof beslis oor jou saak op meriete.",
        "notice_days": "Die ander party het 14 dae vanaf ontvangs van hierdie brief om te betaal of te skik.",
        "sources_title": "Gebaseer op",
        "unsupported_title": "Nog nie in hierdie taal beskikbaar nie",
        "unsupported_body": "Ons het nie 'n vertaalmodel gevind wat hierdie taal goed genoeg hanteer om met 'n regsdokument vertrou te word nie. Eerder as om jou 'n swak vertaling te gee, is ons eerlik daaroor. Jy kan in Engels of Afrikaans voortgaan.",
        "sasl_body": "Suid-Afrikaanse Gebaretaal is 'n gebaretaal sonder 'n geskrewe vorm, dus kan 'n geskrewe brief nie daarin opgestel word nie. Videoleiding word beplan maar is nog nie gebou nie.",
        "mt_banner": "Hierdie bladsy is deur 'n rekenaar vertaal en is nie deur 'n mens nagegaan nie.",
        "delivery_title": "Bewys dat jy dit afgelewer het",
        "delivery_intro": "Voordat jy 'n dagvaarding kan uitreik, moet jy bewys dat die ander party hierdie brief ontvang het. Hoe gaan jy dit aflewer?",
        "delivery_post": "Per geregistreerde pos",
        "delivery_post_hint": "Die poskantoorstrokie is jou bewys.",
        "delivery_personal": "Self, per hand",
        "delivery_personal_hint": "Jy sal 'n beëdigde verklaring nodig hê.",
        "delivery_other": "Op 'n ander manier",
        "delivery_other_hint": "Jy sal 'n beëdigde verklaring nodig hê wat verduidelik hoe.",
        "id_number": "Jou ID- of paspoortnommer",
        "delivery_date": "Datum waarop jy dit afgelewer het",
        "delivery_time": "Tyd waarop jy dit afgelewer het",
        "recipient_name": "Naam van die persoon wat die brief ontvang het",
        "recipient_hint": "As dit 'n winkel was, die naam van wie dit aanvaar het.",
        "delivery_place": "Waar jy dit afgelewer het",
        "other_method": "Hoe het jy dit afgelewer?",
        "make_affidavit": "Berei die beëdigde verklaring voor",
        "affidavit_title": "Beëdigde verklaring (Vorm 5)",
        "affidavit_warning": "Moenie dit nou onderteken nie. Dit is eers geldig wanneer jy dit voor 'n Kommissaris van Ede onderteken.",
        "summons_title": "As hulle nie betaal nie",
        "summons_intro": "Na 14 dae sonder betaling kan jy die volgende stap neem. Willa kan voorberei wat jy op Vorm 1 moet skryf \u2014 die moeilike deel is om jou eis kortliks te beskryf, en dit is wat hierdie doen.",
        "summons_not_a_summons": "Hierdie is nie \'n dagvaarding nie. Slegs die klerk van die hof kan een uitreik. Dit is die blad waaruit jy die amptelike vorm invul.",
        "your_phone": "Jou telefoonnommer",
        "other_phone": "Hul telefoonnommer (indien bekend)",
        "admitted_debt": "Skuld jy hulle iets? (Rand)",
        "admitted_debt_hint": "Los leeg indien nie. Indien wel, kan dit van jou eis afgetrek word.",
        "make_summons": "Berei my Vorm 1-notas voor",
        "making_summons": "Berei voor\u2026",
        "save_title": "Stoor jou eis om later terug te kom",
        "save_intro": "Willa hou niks. As jy later wil voortgaan, stoor \'n l\u00easer op jou eie toestel en laai dit terug wanneer jy terugkeer.",
        "save_file": "Stoor my eis na \'n l\u00easer",
        "load_file": "Laai \'n gestoorde eis",
        "save_pass": "Wagwoord (opsioneel)",
        "save_pass_hint": "As iemand anders hierdie toestel gebruik, stel \'n wagwoord. Willa kan dit nie herwin as jy dit vergeet nie \u2014 die l\u00easer sal verlore wees.",
        "save_shared_warning": "Enigiemand wat hierdie l\u00easer kry, kan jou eis lees tensy jy \'n wagwoord stel.",
        "save_done": "Gestoor. Hou dit iewers waar net jy kan bykom.",
        "load_pass_prompt": "Hierdie l\u00easer het \'n wagwoord. Voer dit in om die eis oop te maak.",
        "load_wrong_pass": "Daardie wagwoord het nie die l\u00easer oopgemaak nie. Gaan dit na en probeer weer.",
        "load_bad_file": "Dit lyk nie soos \'n Willa-l\u00easer nie.",
        "load_done": "Eis gelaai. Jou besonderhede is weer ingevul.",
        "task_title": "Wat het jy vandag nodig?",
        "task_letter": "Skryf \'n brief van aanmaning",
        "task_letter_hint": "Begin hier. Dit is die eerste stap \u2014 jy moet dit stuur voordat jy hof toe kan gaan.",
        "task_affidavit": "Bewys ek het my brief afgelewer",
        "task_affidavit_hint": "Jy het jou brief reeds gestuur en het die be\u00ebdigde verklaring (Vorm 5) nodig.",
        "task_court": "Berei voor vir die hof",
        "task_court_hint": "Die 14 dae is verby en hulle het nie betaal nie. Berei voor wat jy op Vorm 1 skryf.",
        "task_resume": "Gaan voort met \'n gestoorde eis",
        "task_resume_hint": "Laai die l\u00easer wat jy laas gestoor het.",
        "back_to_tasks": "Terug",
        "your_details_for_affidavit": "Die be\u00ebdigde verklaring het jou besonderhede nodig. Vul dit in as dit nie reeds daar is nie.",
        "court_needs_claim": "Die hofvorm het jou eisbesonderhede nodig, insluitend wat gebeur het. Vul dit in en berei dan jou notas voor.",
        "brand_1": "Permanent",
        "brand_2": "Soewerein",
        "brand_3": "Gelyk",
        "hero_kicker": "'n Privaatheid-eerste regsassistent vir die Klein Eisehof",
        "point_1": "5,1 miljard mense word uitgesluit van die regsbeskerming wat hulle toekom.",
        "point_2": "Suid-Afrika is die mees ongelyke land ter w\u00eareld.",
        "point_3": "Regstatus is \'n reg, nie \'n ekonomiese voorreg nie.",
        "point_4": "Ons begin waar die wrywing die hoogste is.",
        "intro_enter": "Tik die sirkel om te begin",
        "intro_listen": "Luister",
        "intro_stop": "Stop",
        "intro_no_voice": "Hierdie toestel het geen stem vir jou taal nie, so Willa kan dit nie hardop lees nie. Die woorde is op die skerm.",
        "explain_title": "Wat hierdie brief sê",
        "explain_note": "Die brief is in Engels omdat dit die taal is wat Suid-Afrikaanse howe gebruik. Hierdie opsomming is in jou taal sodat jy weet wat jy onderteken.",
        "explain_show_en": "Wys dit in Engels",
        "explain_unavailable": "Willa kon nie hierdie opsomming in jou taal maak nie, en sal nie vir jou Engels wys sonder om jou te sê nie.",
        "pending_title": "Binnekort beskikbaar",
        "pending_body": "'n Vertaalmodel wat hierdie taal hanteer word bygevoeg. Dit is nog nie geïnstalleer nie, en ons sê dit eerder vir jou as om vir jou 'n Engelse brief te gee wat jy nie gevra het nie. Engels en Afrikaans werk vandag.",
    },
}


def _machine_strings() -> dict[str, dict[str, str]]:
    """Machine-translated UI strings, built by scripts/build_ui_translations.py.

    Loaded lazily and cached. Absent file is normal — it just means the
    machine-translated languages have not been generated yet, and those
    languages fall back to English per key.
    """
    global _MT_CACHE
    if _MT_CACHE is None:
        import json
        from . import config

        path = config.DATA_DIR / "ui_strings_mt.json"
        try:
            _MT_CACHE = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _MT_CACHE = {}
    return _MT_CACHE


_MT_CACHE: dict[str, dict[str, str]] | None = None


def is_machine_translated(code: str) -> bool:
    """True when the interface for this language came from a model rather than
    a person. The UI says so — someone reading unreviewed output deserves to
    know that is what they are reading."""
    return code not in STRINGS and bool(_machine_strings().get(code))


def strings_for(code: str) -> dict[str, str]:
    """UI strings for a language code.

    Three layers, most trusted first: hand-written, machine-translated,
    English. Per key, so a missing translation degrades one string rather than
    a whole language.
    """
    base = dict(STRINGS["en"])
    base.update(_machine_strings().get(code, {}))
    base.update(STRINGS.get(code, {}))
    return base


def is_draftable(code: str) -> bool:
    """Can we responsibly produce a document in this language *right now*?

    "mt" languages depend on the translation layer. While that is off, offering
    them would mean handing someone an English letter they did not ask for and
    may not read. Better to say not yet.
    """
    from . import config

    lang = BY_CODE.get(code)
    if not lang:
        return False
    if lang["status"] == "native":
        return True
    if lang["status"] == "mt":
        return config.TRANSLATION_AVAILABLE
    return False


def availability_note(code: str) -> str:
    """Why a language is unavailable, for the UI."""
    from . import config

    lang = BY_CODE.get(code)
    if not lang or is_draftable(code):
        return ""
    if lang["status"] == "mt" and not config.TRANSLATION_AVAILABLE:
        return "translation layer not installed yet"
    if lang["status"] == "none":
        return "no trusted model yet"
    if lang["status"] == "nontext":
        return "signed language — no written form"
    return ""
