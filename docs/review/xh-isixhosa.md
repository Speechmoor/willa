# Willa — isiXhosa review

**Language:** isiXhosa (isiXhosa) · `xh`  
**Strings to review:** 93  
**Automated confidence:** checked against a second, independent translation model

## What Willa is

Willa helps someone write a **letter of demand** for the South African Small Claims Court — the formal letter you must send before you can issue a summons. It runs entirely on the user's own device.

The letter itself is always in English, because that is the language South African courts keep their record in. Everything you are reviewing here is the *interface* and a plain-language *explanation* of the letter, so that someone can understand what they are signing.

All of this text was produced by a translation model. **No first-language speaker has read it.** That is what we are asking you to do.

---

## Please look at these first

Automated checking already flagged these. They may be false alarms.

- "Plaintiff" round-trips as **"prosecutor"**, which is criminal-law language. This is a civil matter — nobody is being prosecuted.
- `your_email` renders "optional" as *engacwangciswanga*, which may read closer to "unconfigured".
- `notice_days` appears to say "to pay or to pay" — the English is "pay or settle".
- `pending_title` may be first person ("I will come soon") where it should be "coming shortly".

---

## 1. Legal terms  ← most important

These five words carry the meaning of the document. If one is wrong, the letter can say something its writer did not intend. Please give the word you would actually use in isiXhosa.

| English term | What it means | Correct term in isiXhosa |
|---|---|---|
| **plaintiff** | The person bringing the claim — the one who is owed money and who writes the letter. | |
| **defendant** | The person or business being claimed against — the one who owes the money. | |
| **letter of demand** | The formal written request for payment that must be delivered before a summons can be issued. | |
| **commissioner** | The official who presides over a Small Claims Court hearing. Not a magistrate and not a judge. | |
| **Small Claims Court** | The court itself. Willa currently leaves this in English on the theory that it matches the sign on the building — tell us if that is wrong. | |

---

## 2. Sentences where a mistake is serious

Read these against the English and correct anything that changes the meaning — especially a missing **not**.

### `disclaimer`

**English:** Willa is not a lawyer and this is not legal advice. A Small Claims Court commissioner decides your case on its merits.

**isiXhosa:** UWilla akangommeli yaye oku akusiyo ingcebiso yezomthetho.

**Correction (leave blank if fine):**

> 

### `print_footer`

**English:** Prepared with Willa. Willa is not a lawyer and this is not legal advice. Check every detail before you sign and send this letter.

**isiXhosa:** UWilla akangommeli yaye oku akusiyo ingcebiso yezomthetho, khangela zonke iinkcukacha ngaphambi kokuba usayine uze uthumele le leta.

**Correction (leave blank if fine):**

> 

### `notice_days`

**English:** The other party has 14 days from receiving this letter to pay or settle.

**isiXhosa:** Elinye iqela linentsuku ezili-14 ukusuka ekufumaneni le leta ukuhlawula okanye ukuhlawula.

**Correction (leave blank if fine):**

> 

### `mt_banner`

**English:** This page was translated by a computer and has not been checked by a person. Tell us if something reads wrongly.

**isiXhosa:** Eli phepha liguqulelwe ngekhompyutha yaye alizange lihlolwe ngumntu.

**Correction (leave blank if fine):**

> 

### `explain_note`

**English:** The letter is in English because that is the language South African courts use. This summary is in your language so you know what you are signing.

**isiXhosa:** Le leta ibhalwe ngesiNgesi kuba lulwimi olusetyenziswa ziinkundla zaseMzantsi Afrika.

**Correction (leave blank if fine):**

> 

### `review_hint`

**English:** Read every line. Correct anything that is wrong. You are responsible for what you send.

**isiXhosa:** Funda yonke imigca, lungisa nantoni na engalunganga. Unoxanduva lwento oyithumelayo.

**Correction (leave blank if fine):**

> 

### `local_badge`

**English:** Runs on this device. Nothing is sent anywhere.

**isiXhosa:** Isebenza kwesi sixhobo. Akukho nto ithunyelwa naphi na.

**Correction (leave blank if fine):**

> 

---

## 3. Everything else

Skim these. Mark anything that is wrong, confusing, or would sound strange to someone worried about money. Natural beats literal.

| Key | English | isiXhosa | Correction |
|---|---|---|---|
| `app_title` | Willa | UWilla | |
| `tagline` | Help preparing a Small Claims Court letter of demand | Uncedo ekulungiseleleni ileta yesicelo seNkundla yeeMfuno ezincinci | |
| `choose_language` | Choose your language | Khetha ulwimi lwakho | |
| `step_your_details` | Your details | Iinkcukacha zakho | |
| `step_other_party` | The other party | Elinye iqela | |
| `step_claim` | Your claim | Isicelo sakho | |
| `your_name` | First name | Igama lokuqala | |
| `your_surname` | Surname | Igama lokugqibela | |
| `your_address` | Your address | Idilesi yakho | |
| `your_email` | Your email (optional) | I-imeyile yakho (engacwangciswanga) | |
| `other_name` | Their name or business name | Igama labo okanye igama lorhwebo | |
| `other_surname` | Their surname (if a person) | Igama labo lokugqibela (ukuba ngumntu) | |
| `other_address` | Their address | Idilesi yabo | |
| `other_email` | Their email (if you know it) | I-imeyile yabo (ukuba uyayazi) | |
| `amount` | Amount claimed (Rand) | Isixa esifunwayo (Rand) | |
| `claim_basis` | What happened? | Kwenzeka ntoni? | |
| `claim_basis_hint` | Explain in your own words. What was agreed, what went wrong, and what you are owed. | Chaza ngamazwi akho, oko kuvunyelwene ngako, oko kuphosakeleyo noko ukukutyala. | |
| `agreement_date` | Date of the purchase or agreement | Umhla wokuthenga okanye wesivumelwano | |
| `agreement_date_hint` | When you paid, signed, or agreed. Leave blank if it does not apply. | Xa uhlawule, utyikitye okanye uvumile. | |
| `failure_date` | Date it went wrong | Umhla owaphambukayo | |
| `failure_date_hint` | When the goods failed, the work was not done, or payment fell due. | Xa impahla ingaphumelelanga, umsebenzi awuzange wenziwe, okanye intlawulo yayingahlawulwa. | |
| `generate` | Prepare my letter | Lungiselela ileta yam | |
| `generating` | Preparing your letter… | Ukulungiselela ileta yakho... | |
| `review_title` | Check this before you use it | Jonga oku ngaphambi kokuba uyisebenzise | |
| `download` | Download as text | Khuphela ileta | |
| `save_pdf` | Save as PDF | Gcina njengePDF | |
| `start_over` | Start over | Qala ngokutsha | |
| `sources_title` | Based on | Ngokusekelwe | |
| `unsupported_title` | Not available in this language yet | Ayifumaneki kolu lwimi okwamanje | |
| `unsupported_body` | We have not found a translation model that handles this language well enough to be trusted with a legal document. Rather than give you a bad translation, we are being upfront. You can continue in English or Afrikaans. | Kunokuba sikunike inguqulelo engalunganga, sinyanisekile. Unokuqhubeka ngolwimi lwesiNgesi okanye lwesiAfrikaans. | |
| `sasl_body` | South African Sign Language is a signed language with no written form, so a written letter cannot be produced in it. Video guidance is planned but not built yet. | Ulwimi Lwezandla LwaseMzantsi Afrika lulwimi lwezandla olungenalo uhlobo olubhaliweyo, ngoko ke alunakwenziwa ileta ebhaliweyo kulo. | |
| `delivery_title` | Prove you delivered it | Bonisa ukuba uyinikele | |
| `delivery_intro` | Before you can issue a summons, you must prove the other side received this letter. How will you deliver it? | Ngaphambi kokuba wenze isimemo, umele ungqine ukuba eli leta lifunyenwe licala eliphikisayo. | |
| `delivery_post` | By registered post | Ngeposi ebhalisiweyo | |
| `delivery_post_hint` | The post office receipt is your proof. | Isiqinisekiso sokufumana iofisi yeposi bubungqina bakho. | |
| `delivery_personal` | By hand, myself | Ngokwenza ngesandla, ngokwam | |
| `delivery_personal_hint` | You will need a sworn affidavit. | Uya kudinga isibhengezo esifungelweyo. | |
| `delivery_other` | Some other way | Ngenye indlela | |
| `delivery_other_hint` | You will need a sworn affidavit explaining how. | Uya kudinga isibhengezo esifungelweyo esichaza indlela. | |
| `id_number` | Your ID or passport number | Inombolo yakho yesazisi okanye yepasipoti | |
| `delivery_date` | Date you delivered it | Umhla owawunikela ngawo | |
| `delivery_time` | Time you delivered it | Lifikile ixesha lokuba ulithumele | |
| `recipient_name` | Name of the person who took the letter | Igama lomntu othathe ileta | |
| `recipient_hint` | If it was a shop, the name of whoever accepted it. | Ukuba yayiyivenkile, igama lalowo wayamkelayo. | |
| `delivery_place` | Where you delivered it | Apho wawuyinikela khona | |
| `other_method` | How did you deliver it? | Wawufumana njani? | |
| `make_affidavit` | Prepare the affidavit | Lungiselela ingxelo efungelweyo | |
| `affidavit_title` | Affidavit (Form 5) | Isiqinisekiso (ifom 5) | |
| `affidavit_warning` | Do not sign this yet. It is only valid once you sign it in front of a Commissioner of Oaths. | Musa ukutyikitya oku, kusebenza kuphela xa uyityikitya phambi komkomishinala wezifungo. | |
| `summons_title` | If they do not pay | Ukuba abahlawuli | |
| `summons_intro` | After 14 days with no payment, you can take the next step. Willa can prepare what you need to write on Form 1 — the hard part is describing your claim briefly, and that is what this does. | Emva kweentsuku ezili-14 kungekho ntlawulo, unokuthatha inyathelo elilandelayo. UWilla angalungiselela oko ufuna ukukubhala kwiFom 1  inxalenye enzima kukuchaza ibango lakho ngokufutshane, kwaye yiloo nto eyenzekayo. | |
| `summons_not_a_summons` | This is not a summons. Only the clerk of the court can issue one. This is the sheet you write onto the official form. | Oku akusiyo isimemo, ngummeli wenkundla kuphela onokukhupha isimemo. Eli liphepha olibhalayo kwifom esemthethweni. | |
| `your_phone` | Your phone number | Inombolo yakho yomnxeba | |
| `other_phone` | Their phone number (if you know it) | Inombolo yabo yefowuni (ukuba uyayazi) | |
| `admitted_debt` | Do you owe them anything? (Rand) | Ngaba unetyala kubo? | |
| `admitted_debt_hint` | Leave blank if not. If you do, it can be deducted from your claim. | Yishiye ingenanto ukuba akunjalo. Ukuba uyayenza, inokucutshulwa kwimbongo yakho. | |
| `make_summons` | Prepare my Form 1 notes | Lungiselela amanqaku am eFomu 1 | |
| `making_summons` | Preparing… | Ukulungiselela... | |
| `save_title` | Save your claim to come back to | Gcina isimangalo sakho sokubuyela | |
| `save_intro` | Willa keeps nothing. If you want to carry on later, save a file to your own device and load it back when you return. | Ukuba ufuna ukuqhubeka kamva, gcina ifayile kwisixhobo sakho uze uyilayishe kwakhona xa ubuya. | |
| `save_file` | Save my claim to a file | Gcina isimangalo sam kwifayile | |
| `load_file` | Load a saved claim | Ukulayisha i-claim egciniweyo | |
| `save_pass` | Password (optional) | Iphasiwedi (ngokuzithandela) | |
| `save_pass_hint` | If anyone else uses this device, set a password. Willa cannot recover it if you forget it — the file would be lost. | Ukuba kukho omnye umntu osebenzisa esi sixhobo, cwangcisa iphasiwedi. UWilla akanakuyifumana ukuba uyakulibala  ifayile iya kulahleka. | |
| `save_shared_warning` | Anyone who finds this file can read your claim unless you set a password. | Nabani na oyifumanayo le fayile unokuyifunda ingxelo yakho ngaphandle kokuba ubeke iphasiwedi. | |
| `save_done` | Saved. Keep it somewhere only you can reach. | Yibeke kwindawo ekwazi ukufikelela kuyo kuphela. | |
| `load_pass_prompt` | This file has a password. Enter it to open the claim. | Le fayile inephasiwedi. Yifake ukuze uvule isicelo. | |
| `load_wrong_pass` | That password did not open the file. Check it and try again. | Iphasiwedi ayizange ivule ifayile, khangela uze uzame kwakhona. | |
| `load_bad_file` | That does not look like a Willa file. | Oku akufani nefayile kaWilla. | |
| `load_done` | Claim loaded. Your details have been filled in again. | Iinkcukacha zakho ziphinde zagcwaliswa. | |
| `task_title` | What do you need today? | Yintoni oyifunayo namhlanje? | |
| `task_letter` | Write a letter of demand | Bhala ileta yesicelo | |
| `task_letter_hint` | Start here. This is the first step — you must send this before you can go to court. | Qala apha. Eli linyathelo lokuqala  kufuneka uthumele oku ngaphambi kokuba uye enkundleni. | |
| `task_affidavit` | Prove I delivered my letter | Bonisa ukuba ndiyinikele ileta yam | |
| `task_affidavit_hint` | You have already sent your letter and need the affidavit (Form 5). | Sele uthumele ileta yakho kwaye udinga i-afidavithi (ifom 5). | |
| `task_court` | Prepare for court | Zilungiselele ukuya enkundleni | |
| `task_resume` | Continue a saved claim | Qhubeka nomyalelo ogciniweyo | |
| `task_resume_hint` | Load the file you saved last time. | Faka ifayile oyigcinileyo kwixesha elidlulileyo. | |
| `back_to_tasks` | Back | Buyela Umva | |
| `your_details_for_affidavit` | The affidavit needs your details. Fill these in if they are not already there. | I-afidavithi ifuna iinkcukacha zakho. | |
| `court_needs_claim` | The court form needs your claim details, including what happened. Fill these in, then prepare your notes. | Ifomu yenkundla ifuna iinkcukacha zakho, kuquka oko kwenzekileyo. | |
| `explain_title` | What this letter says | Oko kuthethwa yile leta | |
| `explain_show_en` | Show this in English | Bonisa oku ngesiNgesi | |
| `explain_unavailable` | Willa could not produce this summary in your language, and will not show you English instead without telling you. | UWilla akakwazi ukuvelisa esi sicatshulwa ngolwimi lwakho, yaye akayi kukubonisa isiNgesi ngaphandle kokuba akuxelele. | |
| `pending_title` | Coming shortly | Ndiza kuza kungekudala | |
| `pending_body` | A translation model that handles this language is being added. It is not installed yet, and we would rather tell you that than hand you an English letter you did not ask for. English and Afrikaans work today. | Kuza kongezelelwa imodeli yokuguqulela esebenza kolu lwimi. Akukafakwa okwamanje, yaye singathanda ukukuxelela oko kunokuba sikunike ileta yesiNgesi ongazange uyicele. IsiNgesi nesiAfrikaans zisebenza namhlanje. | |

---

## Tone

The person reading this is usually owed money they need back, and may be under real pressure. The writing should be plain, calm and respectful — not officious, not falsely reassuring, and not so formal that it becomes hard to follow.

If a sentence is technically accurate but sounds wrong coming from a service meant to help, please say so. That is as useful as a mistranslation.

## Sending it back

Fill in the blanks and return the file. Corrections go straight into `data/ui_strings_mt.json`, and rebuilding will not overwrite them.
