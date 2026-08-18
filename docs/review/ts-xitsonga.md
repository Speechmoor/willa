# Willa — Xitsonga review

**Language:** Xitsonga (Xitsonga) · `ts`  
**Strings to review:** 93  
**Automated confidence:** checked against a second, independent translation model

## What Willa is

Willa helps someone write a **letter of demand** for the South African Small Claims Court — the formal letter you must send before you can issue a summons. It runs entirely on the user's own device.

The letter itself is always in English, because that is the language South African courts keep their record in. Everything you are reviewing here is the *interface* and a plain-language *explanation* of the letter, so that someone can understand what they are signing.

All of this text was produced by a translation model. **No first-language speaker has read it.** That is what we are asking you to do.

---

## Please look at these first

Automated checking already flagged these. They may be false alarms.

- The disclaimer round-trips into English as **"Willa WAS a lawyer"** instead of "Willa is not a lawyer". Please check the negation carefully — this is the sentence that says Willa is not giving legal advice, so losing the "not" reverses something important.

---

## 1. Legal terms  ← most important

These five words carry the meaning of the document. If one is wrong, the letter can say something its writer did not intend. Please give the word you would actually use in Xitsonga.

| English term | What it means | Correct term in Xitsonga |
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

**Xitsonga:** Willa a hi gqweta naswona leswi a hi switsundzuxo swa le nawini.

**Correction (leave blank if fine):**

> 

### `print_footer`

**English:** Prepared with Willa. Willa is not a lawyer and this is not legal advice. Check every detail before you sign and send this letter.

**Xitsonga:** Willa a hi gqweta naswona leswi a hi switsundzuxo swa nawu. Kambisisa vuxokoxoko hinkwabyo u nga si sayina ni ku rhumela papila leri.

**Correction (leave blank if fine):**

> 

### `notice_days`

**English:** The other party has 14 days from receiving this letter to pay or settle.

**Xitsonga:** Munhu un'wana u ni masiku ya 14 ku sukela loko a kume papila leri leswaku a hakela kumbe a lulamisa timhaka.

**Correction (leave blank if fine):**

> 

### `mt_banner`

**English:** This page was translated by a computer and has not been checked by a person. Tell us if something reads wrongly.

**Xitsonga:** Tluka leri ri hundzuluxeriwe hi khompyuta naswona a ku na munhu loyi a ri kambisiseke.

**Correction (leave blank if fine):**

> 

### `explain_note`

**English:** The letter is in English because that is the language South African courts use. This summary is in your language so you know what you are signing.

**Xitsonga:** Papila leri ri tsariwe hi Xinghezi hikuva hi rona ririmi leri tirhisiwaka hi tihuvo ta Afrika Dzonga.

**Correction (leave blank if fine):**

> 

### `review_hint`

**English:** Read every line. Correct anything that is wrong. You are responsible for what you send.

**Xitsonga:** Hlaya layini yin'wana ni yin'wana, lulamisa xin'wana ni xin'wana lexi hoxeke.

**Correction (leave blank if fine):**

> 

### `local_badge`

**English:** Runs on this device. Nothing is sent anywhere.

**Xitsonga:** Xitirhisiwa lexi a xi rhumeriwi kun'wana ni kun'wana.

**Correction (leave blank if fine):**

> 

---

## 3. Everything else

Skim these. Mark anything that is wrong, confusing, or would sound strange to someone worried about money. Natural beats literal.

| Key | English | Xitsonga | Correction |
|---|---|---|---|
| `app_title` | Willa | Willa | |
| `tagline` | Help preparing a Small Claims Court letter of demand | Pfuna eku lunghiseleleni ka papila ra xikombelo ra huvo ya swivilelo leswitsongo | |
| `choose_language` | Choose your language | Hlawula ririmi ra wena | |
| `step_your_details` | Your details | Vuxokoxoko bya wena | |
| `step_other_party` | The other party | Ntlawa wun'wana | |
| `step_claim` | Your claim | Xikombelo xa wena | |
| `your_name` | First name | Vito ro sungula | |
| `your_surname` | Surname | Vito ra ndyangu | |
| `your_address` | Your address | Adirese ya wena | |
| `your_email` | Your email (optional) | E-mail ya wena (yi nga bohi) | |
| `other_name` | Their name or business name | Vito ra vona kumbe vito ra bindzu ra vona | |
| `other_surname` | Their surname (if a person) | Vito ra vona (loko ku ri munhu) | |
| `other_address` | Their address | Adirese ya vona | |
| `other_email` | Their email (if you know it) | E-mail ya vona (loko u yi tiva) | |
| `amount` | Amount claimed (Rand) | Mali leyi kombisiweke (Rand) | |
| `claim_basis` | What happened? | Xana ku humelele yini? | |
| `claim_basis_hint` | Explain in your own words. What was agreed, what went wrong, and what you are owed. | Hlamusela hi marito ya wena n'wini. | |
| `agreement_date` | Date of the purchase or agreement | Siku ra ku xava kumbe ntwanano | |
| `agreement_date_hint` | When you paid, signed, or agreed. Leave blank if it does not apply. | Loko u hakerile, u sayine kumbe u pfumerile. | |
| `failure_date` | Date it went wrong | Siku leri swi nga fambiki kahle ha rona | |
| `failure_date_hint` | When the goods failed, the work was not done, or payment fell due. | Loko nhundzu yi nga tirhi kahle, ntirho a wu nga endliwi kumbe hakelo a yi fanele yi hakeriwa. | |
| `generate` | Prepare my letter | Lunghiselela papila ra mina | |
| `generating` | Preparing your letter… | Ku lunghiselela papila ra wena... | |
| `review_title` | Check this before you use it | Kambisisa leswi u nga si swi tirhisa | |
| `download` | Download as text | Kopa papila | |
| `save_pdf` | Save as PDF | Hlayisa tanihi PDF | |
| `start_over` | Start over | Sungula hi vuntshwa | |
| `sources_title` | Based on | Hi ku ya hi | |
| `unsupported_title` | Not available in this language yet | A ya ha kumeki hi ririmi leri | |
| `unsupported_body` | We have not found a translation model that handles this language well enough to be trusted with a legal document. Rather than give you a bad translation, we are being upfront. You can continue in English or Afrikaans. | Ematshan'weni yo ku nyika vuhundzuluxeri byo biha, hi vulavula na wena hi ku kongoma. U nga ya emahlweni hi Xinghezi kumbe hi Afrikaans. | |
| `sasl_body` | South African Sign Language is a signed language with no written form, so a written letter cannot be produced in it. Video guidance is planned but not built yet. | Ririmi ra Mavoko ra le Afrika Dzonga i ririmi ra mavoko leri nga riki na xivumbeko lexi tsariweke, hikwalaho ku hava papila leri tsariweke eka rona. | |
| `delivery_title` | Prove you delivered it | Kombisa leswaku u yi rhumerile | |
| `delivery_intro` | Before you can issue a summons, you must prove the other side received this letter. How will you deliver it? | Loko u nga si humesa xirhambo xo ya ehubyeni, u fanele u kombisa leswaku u kume papila leri. | |
| `delivery_post` | By registered post | Hi poso leyi tsarisiweke | |
| `delivery_post_hint` | The post office receipt is your proof. | Xitifiketi xa poso i vumbhoni bya wena. | |
| `delivery_personal` | By hand, myself | Hi voko, mina hi ndzexe | |
| `delivery_personal_hint` | You will need a sworn affidavit. | U ta lava xitiyisekiso lexi hlambanyiweke. | |
| `delivery_other` | Some other way | Hi ndlela yin'wana | |
| `delivery_other_hint` | You will need a sworn affidavit explaining how. | U ta lava xitiyisekiso lexi hlambanyiweke lexi hlamuselaka ndlela leyi. | |
| `id_number` | Your ID or passport number | Nomboro ya wena ya vutitivisi kumbe ya pasi | |
| `delivery_date` | Date you delivered it | Siku leri u ri rhumeleke ha rona | |
| `delivery_time` | Time you delivered it | Nkarhi lowu a wu ta wu nyikela ha wona | |
| `recipient_name` | Name of the person who took the letter | Vito ra munhu loyi a tekeke papila | |
| `recipient_hint` | If it was a shop, the name of whoever accepted it. | Loko a ku ri xitolo, vito ra loyi a xi amukeleke. | |
| `delivery_place` | Where you delivered it | Laha u yi rhumeleke kona | |
| `other_method` | How did you deliver it? | Xana u yi tise njhani? | |
| `make_affidavit` | Prepare the affidavit | Lunghiselela xitiviso lexi hlambanyiweke | |
| `affidavit_title` | Affidavit (Form 5) | Xitiviso lexi hlambanyiweke (Fomo 5) | |
| `affidavit_warning` | Do not sign this yet. It is only valid once you sign it in front of a Commissioner of Oaths. | A wu fanelanga u sayina papila leri, kambe ri ta tirha ntsena loko u ri sayina emahlweni ka Mukongomisi wa Swihlambanyo. | |
| `summons_title` | If they do not pay | Loko va nga hakeli | |
| `summons_intro` | After 14 days with no payment, you can take the next step. Willa can prepare what you need to write on Form 1 — the hard part is describing your claim briefly, and that is what this does. | Endzhaku ka masiku ya 14 u nga hakeli, u nga teka goza leri landzelaka. Willa a nga lunghiselela leswi u faneleke u swi tsala eka Fomo 1  xiphemu xo tika i ku hlamusela xikombelo xa wena hi ku komisa, naswona leswi hi swona leswi endlekaka. | |
| `summons_not_a_summons` | This is not a summons. Only the clerk of the court can issue one. This is the sheet you write onto the official form. | Lexi a hi xirhambo, kambe i matsalana wa huvo ntsena loyi a nga xi humesaka. | |
| `your_phone` | Your phone number | Nomboro ya wena ya riqingho | |
| `other_phone` | Their phone number (if you know it) | Nomboro ya vona ya riqingho (loko u yi tiva) | |
| `admitted_debt` | Do you owe them anything? (Rand) | Xana u va kolota swo karhi? | |
| `admitted_debt_hint` | Leave blank if not. If you do, it can be deducted from your claim. | Loko u nga swi endli, swi nga hungutiwa eka xikweleti xa wena. | |
| `make_summons` | Prepare my Form 1 notes | Lunghiselela tifomo ta mina ta Fomo 1 | |
| `making_summons` | Preparing… | Ku lunghiselela... | |
| `save_title` | Save your claim to come back to | Hlayisa leswi u swi vulaka leswaku u ta tlhela u vuya | |
| `save_intro` | Willa keeps nothing. If you want to carry on later, save a file to your own device and load it back when you return. | Loko u lava ku ya emahlweni hi ku famba ka nkarhi, hlayisa fayele eka xitirhisiwa xa wena kutani u yi rhumela loko u vuya. | |
| `save_file` | Save my claim to a file | Hlayisa xivilelo xa mina eka phepha-hungu | |
| `load_file` | Load a saved claim | Tisa xikombelo lexi hlayisiweke | |
| `save_pass` | Password (optional) | Password (yi nga bohi) | |
| `save_pass_hint` | If anyone else uses this device, set a password. Willa cannot recover it if you forget it — the file would be lost. | Loko un'wana a tirhisa xitirhisiwa lexi, veka password. Willa a nge yi kumi loko u yi rivala  fayili yi ta lahleka. | |
| `save_shared_warning` | Anyone who finds this file can read your claim unless you set a password. | Un'wana ni un'wana loyi a kumaka fayili leyi a nga hlaya xikombelo xa wena handle ka loko u veke rito ra wena ra xihundla. | |
| `save_done` | Saved. Keep it somewhere only you can reach. | Yi hlayise endhawini leyi nga fikeleriwaka hi wena ntsena. | |
| `load_pass_prompt` | This file has a password. Enter it to open the claim. | Fayili leyi yi na rito ra xihundla. Nghena eka rona leswaku u pfula xikombelo. | |
| `load_wrong_pass` | That password did not open the file. Check it and try again. | Password yoleyo a yi yi pfulelanga fayili. Kambisisa kutani u tlhela u ringeta. | |
| `load_bad_file` | That does not look like a Willa file. | Sweswo a swi fani ni fayili ya Willa. | |
| `load_done` | Claim loaded. Your details have been filled in again. | Xirhambo xi tatiwile, vuxokoxoko bya wena byi tatiwile nakambe. | |
| `task_title` | What do you need today? | Xana u lava yini namuntlha? | |
| `task_letter` | Write a letter of demand | Tsala papila ra xikombelo | |
| `task_letter_hint` | Start here. This is the first step — you must send this before you can go to court. | Leswi i goza ro sungula leri u faneleke u ri rhumela u nga si ya ehubyeni. | |
| `task_affidavit` | Prove I delivered my letter | Kombisa leswaku ndzi rhumele papila ra mina | |
| `task_affidavit_hint` | You have already sent your letter and need the affidavit (Form 5). | U rhumele papila ra wena naswona u lava xitiviso (Fomu ya 5). | |
| `task_court` | Prepare for court | Tilunghiselele ku ya ehubyeni | |
| `task_resume` | Continue a saved claim | Hambeta u endla xikombelo lexi hlayisiweke | |
| `task_resume_hint` | Load the file you saved last time. | Hlayisa fayili leyi u yi hlayiseke enkarhini lowu hundzeke. | |
| `back_to_tasks` | Back | Ku Tlhelela eNdzhaku | |
| `your_details_for_affidavit` | The affidavit needs your details. Fill these in if they are not already there. | Xitifiketi lexi xi lava vuxokoxoko bya wena. | |
| `court_needs_claim` | The court form needs your claim details, including what happened. Fill these in, then prepare your notes. | Fomo ya le hubyeni yi lava vuxokoxoko bya xikombelo xa wena, ku katsa ni leswi humeleleke. | |
| `explain_title` | What this letter says | Leswi papila leri ri swi vulaka | |
| `explain_show_en` | Show this in English | Kombisa leswi hi Xinghezi | |
| `explain_unavailable` | Willa could not produce this summary in your language, and will not show you English instead without telling you. | Willa a nge swi koti ku humesa nkatsakanyo lowu hi ririmi ra wena, naswona a nge ku kombisi Xinghezi handle ko ku byela. | |
| `pending_title` | Coming shortly | Ku nga ri khale | |
| `pending_body` | A translation model that handles this language is being added. It is not installed yet, and we would rather tell you that than hand you an English letter you did not ask for. English and Afrikaans work today. | Ku engeteriwa xivumbeko xa vuhundzuluxeri lexi tirhisaka ririmi leri. A xi si nghenisiwa naswona hi tsakela ku ku byela sweswo ematshan'weni yo ku nyika papila ra Xinghezi leri u nga ri kombelangiki. | |

---

## Tone

The person reading this is usually owed money they need back, and may be under real pressure. The writing should be plain, calm and respectful — not officious, not falsely reassuring, and not so formal that it becomes hard to follow.

If a sentence is technically accurate but sounds wrong coming from a service meant to help, please say so. That is as useful as a mistranslation.

## Sending it back

Fill in the blanks and return the file. Corrections go straight into `data/ui_strings_mt.json`, and rebuilding will not overwrite them.
