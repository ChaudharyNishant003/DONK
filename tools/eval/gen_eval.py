"""Generate DONK's labelled eval set (PRD section 9).

    python tools/eval/gen_eval.py  ->  tools/eval/utterances.jsonl

400 utterances: 160 Hinglish, 140 Hindi (Devanagari), 100 English. Each carries the
typed labels System 1 answers (intent, domain, kind, tool, needs_llm, urgency, lang)
and the entities the deterministic normaliser must extract. Relative dates are resolved
against REF_TIME. The output is deterministic (fixed seed), so the split never moves.

Labels follow PRD S1-1, plus one extra tool value, `log_metric`, for health readings
(the agent already has that tool; System 1 can file readings without the model).
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

REF_TIME = "2026-10-07T09:30:00+05:30"  # Wednesday
SEED = 20261007
OUT = Path(__file__).with_name("utterances.jsonl")
LANG_QUOTA = {"hinglish": 160, "hindi": 140, "english": 100}

# ---------------------------------------------------------------- slot values
# (english, hinglish, hindi, resolved)
DATES = [
    ("today", "aaj", "आज", "2026-10-07"),
    ("tomorrow", "kal", "कल", "2026-10-08"),
    ("the day after tomorrow", "parso", "परसों", "2026-10-09"),
    ("on Friday", "Friday ko", "शुक्रवार को", "2026-10-09"),
    ("on Saturday", "Saturday ko", "शनिवार को", "2026-10-10"),
    ("this Sunday", "is Sunday", "इस रविवार", "2026-10-11"),
    ("next Monday", "agle Monday", "अगले सोमवार", "2026-10-12"),
    ("on the 15th", "15 tareekh ko", "15 तारीख को", "2026-10-15"),
    ("on 20 October", "20 October ko", "20 अक्टूबर को", "2026-10-20"),
]
DEADLINES = [
    ("by tomorrow", "kal tak", "कल तक", "2026-10-08"),
    ("by Friday", "Friday tak", "शुक्रवार तक", "2026-10-09"),
    ("by Sunday", "Sunday tak", "रविवार तक", "2026-10-11"),
    ("by next Monday", "agle Monday tak", "अगले सोमवार तक", "2026-10-12"),
    ("by the 15th", "15 tareekh tak", "15 तारीख तक", "2026-10-15"),
    ("by the end of the month", "mahine ke end tak", "महीने के आख़िर तक", "2026-10-31"),
]
TIMES = [
    ("at 10 am", "subah 10 baje", "सुबह 10 बजे", "10:00"),
    ("at 6 pm", "shaam 6 baje", "शाम 6 बजे", "18:00"),
    ("at 2:15 pm", "sava do baje", "सवा दो बजे", "14:15"),
    ("at 2:30 pm", "dhai baje", "ढाई बजे", "14:30"),
    ("at 9 pm", "raat 9 baje", "रात 9 बजे", "21:00"),
    ("at 1 pm", "dopahar 1 baje", "दोपहर 1 बजे", "13:00"),
    ("at 7 am", "subah 7 baje", "सुबह 7 बजे", "07:00"),
    ("at 11:30 am", "saade gyarah baje", "साढ़े ग्यारह बजे", "11:30"),
    ("at 4:45 pm", "paune paanch baje", "पौने पाँच बजे", "16:45"),
]
AMOUNTS = [
    ("2000", "2000", "2000", 200000),
    ("2k", "2k", "दो हज़ार", 200000),
    ("500", "paanch sau", "पाँच सौ", 50000),
    ("250", "dhai sau", "ढाई सौ", 25000),
    ("1.5 lakh", "dedh lakh", "डेढ़ लाख", 15000000),
    ("1,800", "1800", "1800", 180000),
    ("12,500", "saade baarah hazaar", "साढ़े बारह हज़ार", 1250000),
    ("450", "450", "450", 45000),
    ("3,000", "teen hazaar", "तीन हज़ार", 300000),
    ("₹750", "750 rupaye", "750 रुपये", 75000),
    ("5k", "5k", "पाँच हज़ार", 500000),
]
# (latin name used in English and Hinglish, Devanagari name)
FRIENDS = [
    ("Kabir", "कबीर"), ("Ravi", "रवि"), ("Anita", "अनीता"), ("Meera", "मीरा"),
    ("Arjun", "अर्जुन"), ("Priya", "प्रिया"), ("Rohit", "रोहित"), ("Neha", "नेहा"),
    ("Vikram", "विक्रम"), ("Sharma ji", "शर्मा जी"), ("Pooja", "पूजा"), ("Sameer", "समीर"),
]
FAMILY = [
    ("Maa", "माँ"), ("Papa", "पापा"), ("Bhaiya", "भैया"), ("Didi", "दीदी"),
    ("Dadi", "दादी"), ("Chacha ji", "चाचा जी"),
]

LANGS = ("english", "hinglish", "hindi")


def L(lang: str, slot: tuple) -> str:
    return slot[LANGS.index(lang)]


def person(lang: str, p: tuple) -> str:
    return p[1] if lang == "hindi" else p[0]


def when(date: str, time: str | None) -> str:
    return f"{date}T{time}" if time else date


def urgency_for(date: str | None) -> str:
    if not date:
        return "low"
    days = int(date[8:10]) - 7 if date.startswith("2026-10") else 99
    return "high" if days <= 0 else "medium" if days <= 2 else "low"


# ---------------------------------------------------------------- generators
# Each generator takes (rng, lang) and returns (text, labels).

TASKS = [
    # (kind, english phrase, hinglish phrase, hindi phrase)
    ("errand", "go to the bank", "bank jaana hai", "बैंक जाना है"),
    ("admin", "renew the car insurance", "car insurance renew karni hai", "गाड़ी का बीमा रिन्यू करना है"),
    ("errand", "pick up Maa's medicines", "Maa ki dawai leni hai", "माँ की दवाई लेनी है"),
    ("chore", "get the AC serviced", "AC ki service karwani hai", "एसी की सर्विस करवानी है"),
    ("admin", "file the ITR", "ITR file karna hai", "आईटीआर फ़ाइल करना है"),
    ("call", "call the plumber", "plumber ko call karna hai", "प्लंबर को फ़ोन करना है"),
    ("errand", "buy vegetables", "sabzi leni hai", "सब्ज़ी लेनी है"),
    ("chore", "clean the balcony", "balcony saaf karni hai", "बालकनी साफ़ करनी है"),
    ("admin", "update the KYC at the bank", "bank mein KYC update karna hai", "बैंक में केवाईसी अपडेट करना है"),
    ("call", "call the gas agency", "gas agency ko phone karna hai", "गैस एजेंसी को फ़ोन करना है"),
    ("todo", "book train tickets for Diwali", "Diwali ke train tickets book karne hain", "दिवाली के ट्रेन टिकट बुक करने हैं"),
    ("errand", "collect the dry cleaning", "dry cleaning se kapde lane hain", "ड्राई क्लीनिंग से कपड़े लाने हैं"),
    ("todo", "send the passport photos", "passport photos bhejni hain", "पासपोर्ट फ़ोटो भेजनी हैं"),
    ("chore", "get the car washed", "gaadi dhulwani hai", "गाड़ी धुलवानी है"),
]


def gen_task(rng, lang):
    kind, en, hl, hi = rng.choice(TASKS)
    d = rng.choice(DATES)
    t = rng.choice(TIMES) if rng.random() < 0.6 else None
    date_s, time_s = L(lang, d), (L(lang, t) if t else "")
    if lang == "english":
        text = rng.choice([
            f"Remind me to {en} {date_s} {time_s}",
            f"I have to {en} {date_s} {time_s}",
            f"{en[0].upper() + en[1:]} {date_s} {time_s}",
        ])
    elif lang == "hinglish":
        text = rng.choice([
            f"{date_s} {time_s} {hl}",
            f"{date_s} {time_s} {hl}, yaad dila dena",
            f"Yaad dilana {date_s} {time_s} {hl}",
        ])
    else:
        text = rng.choice([
            f"{date_s} {time_s} {hi}",
            f"{date_s} {time_s} {hi}, याद दिला देना",
            f"याद दिलाना {date_s} {time_s} {hi}",
        ])
    return text, dict(intent="capture", domain="task", kind=kind, tool="add_item",
                      urgency=urgency_for(d[3]),
                      entities={"due": when(d[3], t[3] if t else None)})


MEET_WORK = [
    ("client call with Mehta & Co", "Mehta & Co ke saath client call hai", "मेहता एंड कंपनी के साथ क्लाइंट कॉल है"),
    ("the design review", "design review meeting hai", "डिज़ाइन रिव्यू मीटिंग है"),
    ("a standup with the team", "team ke saath standup hai", "टीम के साथ स्टैंडअप है"),
    ("the quarterly review", "quarterly review hai", "तिमाही समीक्षा की मीटिंग है"),
]


def gen_meeting(rng, lang):
    d, t = rng.choice(DATES[:7]), rng.choice(TIMES)
    p = rng.choice(FRIENDS)
    if rng.random() < 0.5:
        en, hl, hi = rng.choice(MEET_WORK)
        kind = "work"
        text = {
            "english": f"{en[0].upper() + en[1:]} {L(lang, d)} {L(lang, t)}",
            "hinglish": f"{L(lang, d)} {L(lang, t)} {hl}",
            "hindi": f"{L(lang, d)} {L(lang, t)} {hi}",
        }[lang]
        ents = {"start": when(d[3], t[3])}
    else:
        kind = "personal"
        name = person(lang, p)
        text = {
            "english": rng.choice([f"Coffee with {name} {L(lang, d)} {L(lang, t)}",
                                   f"Dinner with {name} {L(lang, d)} {L(lang, t)}"]),
            "hinglish": rng.choice([f"{L(lang, d)} {L(lang, t)} {name} ke saath coffee",
                                    f"{L(lang, d)} {L(lang, t)} {name} se milna hai"]),
            "hindi": rng.choice([f"{L(lang, d)} {L(lang, t)} {name} के साथ कॉफ़ी",
                                 f"{L(lang, d)} {L(lang, t)} {name} से मिलना है"]),
        }[lang]
        ents = {"start": when(d[3], t[3]), "person": p[0]}
    return text, dict(intent="capture", domain="meeting", kind=kind, tool="add_item",
                      urgency=urgency_for(d[3]), entities=ents)


REASONS = [
    ("for the cab", "cab ke liye", "कैब के लिए"),
    ("for lunch", "lunch ke liye", "लंच के लिए"),
    ("for the concert tickets", "concert tickets ke liye", "कॉन्सर्ट टिकट के लिए"),
    ("for rent", "rent ke liye", "किराए के लिए"),
    ("", "", ""),
]


def gen_money(rng, lang):
    a, p, r = rng.choice(AMOUNTS), rng.choice(FRIENDS), rng.choice(REASONS)
    name, amt, why = person(lang, p), L(lang, a), L(lang, r)
    kind = rng.choice(["lent", "lent", "borrowed", "bill", "bill", "split"])
    ents = {"amount_paise": a[3]}
    urgency = "low"
    if kind == "lent":
        text = {
            "english": rng.choice([f"Lent {name} {amt} {why}", f"I gave {name} {amt} {why}"]),
            "hinglish": rng.choice([f"{name} ko {why} {amt} diye", f"{name} ko {amt} udhaar diye {why}"]),
            "hindi": rng.choice([f"{name} को {why} {amt} दिए", f"{name} को {amt} उधार दिए {why}"]),
        }[lang]
        ents.update(person=p[0], direction="owed_to_me")
    elif kind == "borrowed":
        text = {
            "english": rng.choice([f"I owe {name} {amt} {why}", f"Borrowed {amt} from {name} {why}"]),
            "hinglish": rng.choice([f"{name} se {amt} liye {why}", f"{name} ko {amt} lautane hain"]),
            "hindi": rng.choice([f"{name} से {amt} लिए {why}", f"{name} को {amt} लौटाने हैं"]),
        }[lang]
        ents.update(person=p[0], direction="i_owe")
    elif kind == "bill":
        bill = rng.choice([("electricity bill", "bijli ka bill", "बिजली का बिल"),
                           ("credit card bill", "credit card ka bill", "क्रेडिट कार्ड का बिल"),
                           ("internet bill", "wifi ka bill", "इंटरनेट का बिल"),
                           ("phone bill", "phone ka bill", "फ़ोन का बिल")])
        d = rng.choice(DEADLINES)
        a = rng.choice([x for x in AMOUNTS if x[3] <= 500000])  # bills are not lakhs
        amt = L(lang, a)
        ents["amount_paise"] = a[3]
        text = {
            "english": f"{bill[0][0].upper() + bill[0][1:]} of {amt} due {d[0]}",
            "hinglish": f"{bill[1]} {amt}, {d[1]} bharna hai",
            "hindi": f"{bill[2]} {amt}, {d[2]} भरना है",
        }[lang]
        ents.update(due=d[3], direction="i_owe")
        urgency = urgency_for(d[3])
    else:
        text = {
            "english": f"Paid {amt} for dinner, {name} owes me half",
            "hinglish": f"Dinner ke {amt} maine diye, {name} ka aadha hissa baaki hai",
            "hindi": f"डिनर के {amt} मैंने दिए, {name} का आधा हिस्सा बाकी है",
        }[lang]
        ents = {"amount_paise": a[3] // 2, "person": p[0], "direction": "owed_to_me"}
    return " ".join(text.split()), dict(intent="capture", domain="money", kind=kind,
                                        tool="add_item", urgency=urgency, entities=ents)


PROMISE_BY_ME = [
    ("send {p} the deck", "{p} ko deck bhejna hai", "{p} को डेक भेजना है"),
    ("return {p}'s book", "{p} ki book lautani hai", "{p} की किताब लौटानी है"),
    ("help {p} move house", "{p} ki shifting mein help karni hai", "{p} की शिफ़्टिंग में मदद करनी है"),
    ("share the photos with {p}", "{p} ko photos bhejni hain", "{p} को फ़ोटो भेजनी हैं"),
]
PROMISE_TO_ME = [
    ("{p} said they will return my camera", "{p} ne kaha camera lauta dega", "{p} ने कहा कैमरा लौटा देगा"),
    ("{p} promised to send the invoice", "{p} invoice bhejne wala hai", "{p} इनवॉइस भेजने वाला है"),
    ("{p} will pay me back", "{p} paise lautayega", "{p} पैसे लौटाएगा"),
]


def gen_promise(rng, lang):
    p, d = rng.choice(FRIENDS), rng.choice(DEADLINES)
    name = person(lang, p)
    if rng.random() < 0.58:
        tpl, kind, direction = rng.choice(PROMISE_BY_ME), "by_me", "by_me"
        body = L(lang, tpl).format(p=name)
        text = {"english": f"I promised to {body} {d[0]}", "hinglish": f"{d[1]} {body}, promise kiya hai",
                "hindi": f"{d[2]} {body}, वादा किया है"}[lang]
    else:
        tpl, kind, direction = rng.choice(PROMISE_TO_ME), "to_me", "to_me"
        body = L(lang, tpl).format(p=name)
        text = {"english": f"{body} {d[0]}", "hinglish": f"{body} {d[1]}", "hindi": f"{body} {d[2]}"}[lang]
    return text, dict(intent="capture", domain="promise", kind=kind, tool="add_item",
                      urgency=urgency_for(d[3]),
                      entities={"due": d[3], "person": p[0], "direction": direction})


IDEAS = [
    ("business", "a verified home-services directory for Tier-2 cities",
     "Tier-2 cities ke liye verified home services directory", "टियर-2 शहरों के लिए वेरिफ़ाइड होम सर्विस डायरेक्टरी"),
    ("product", "a voice-first expense splitter", "voice se chalne wala expense splitter app",
     "आवाज़ से चलने वाला ख़र्च बाँटने वाला ऐप"),
    ("content", "a weekly newsletter about building in public", "building in public pe weekly newsletter",
     "बिल्डिंग इन पब्लिक पर साप्ताहिक न्यूज़लेटर"),
    ("personal", "learn the tabla before 35", "35 se pehle tabla seekhna", "35 से पहले तबला सीखना"),
    ("someday", "cycle from Manali to Leh", "Manali se Leh cycle se jaana", "मनाली से लेह साइकिल से जाना"),
    ("content", "a reel series on Indian street food", "Indian street food pe reel series",
     "भारतीय स्ट्रीट फ़ूड पर रील सीरीज़"),
]


def gen_idea(rng, lang):
    kind, en, hl, hi = rng.choice(IDEAS)
    text = {
        "english": rng.choice([f"Idea: {en}", f"What if we built {en}", f"New idea, {en}"]),
        "hinglish": rng.choice([f"Idea: {hl}", f"Ek idea aaya, {hl}", f"Socha hai {hl}"]),
        "hindi": rng.choice([f"आइडिया: {hi}", f"एक आइडिया आया, {hi}"]),
    }[lang]
    return text, dict(intent="capture", domain="idea", kind=kind, tool="add_item",
                      urgency="low", entities={})


WORK = [
    ("deliverable", "the proposal for Mehta & Co is due {d}", "Mehta & Co ka proposal {d} dena hai",
     "मेहता एंड कंपनी का प्रपोज़ल {d} देना है"),
    ("followup", "follow up with {p} about the contract {d}", "{d} {p} se contract ke baare mein follow up karna hai",
     "{d} {p} से कॉन्ट्रैक्ट के बारे में फ़ॉलो अप करना है"),
    ("goal", "goal: close three new clients {d}", "goal hai {d} teen naye clients", "लक्ष्य है {d} तीन नए क्लाइंट"),
]


def gen_work(rng, lang):
    kind, en, hl, hi = rng.choice(WORK)
    d, p = rng.choice(DEADLINES), rng.choice(FRIENDS)
    text = L(lang, (en, hl, hi)).format(d=L(lang, d), p=person(lang, p))
    ents = {"due": d[3]}
    if "{p}" in en:
        ents["person"] = p[0]
    return text[0].upper() + text[1:], dict(intent="capture", domain="work", kind=kind,
                                            tool="add_item", urgency=urgency_for(d[3]), entities=ents)


def gen_health(rng, lang):
    d, t = rng.choice(DATES[:7]), rng.choice(TIMES)
    choice = rng.choice(["appointment", "appointment", "medication", "routine"])
    if choice == "appointment":
        doc = rng.choice([("dentist", "dentist", "डेंटिस्ट"), ("eye check-up", "aankhon ka check-up", "आँखों का चेकअप"),
                          ("blood test", "blood test", "ब्लड टेस्ट")])
        text = {"english": f"{doc[0][0].upper() + doc[0][1:]} appointment {L(lang, d)} {L(lang, t)}",
                "hinglish": f"{L(lang, d)} {L(lang, t)} {doc[1]} ka appointment hai",
                "hindi": f"{L(lang, d)} {L(lang, t)} {doc[2]} का अपॉइंटमेंट है"}[lang]
        ents = {"start": when(d[3], t[3])}
        urg = urgency_for(d[3])
    elif choice == "medication":
        text = {"english": "Take vitamin D every Sunday morning",
                "hinglish": rng.choice(["Har raat sone se pehle BP ki goli leni hai", "Har Sunday subah vitamin D leni hai"]),
                "hindi": rng.choice(["हर रात सोने से पहले बीपी की गोली लेनी है", "हर रविवार सुबह विटामिन डी लेनी है"])}[lang]
        ents, urg = {}, "low"
    else:
        text = {"english": "Start a 20 minute walk every evening",
                "hinglish": "Roz shaam ko 20 minute walk karni hai",
                "hindi": "रोज़ शाम को 20 मिनट टहलना है"}[lang]
        ents, urg = {}, "low"
    return text, dict(intent="capture", domain="health", kind=choice, tool="add_item",
                      urgency=urg, entities=ents)


def gen_metric(rng, lang):
    m = rng.choice([
        ("water_ml", 500, "Drank 2 glasses of water", "2 glass paani piya", "2 गिलास पानी पिया"),
        ("water_ml", 1000, "Had a litre of water", "ek litre paani piya", "एक लीटर पानी पिया"),
        ("sleep_hours", 7.5, "Slept seven and a half hours", "saade saat ghante soya", "साढ़े सात घंटे सोया"),
        ("sleep_hours", 6, "Got 6 hours of sleep", "6 ghante ki neend hui", "6 घंटे की नींद हुई"),
        ("steps", 8200, "Walked 8200 steps today", "aaj 8200 steps chala", "आज 8200 क़दम चला"),
        ("weight_kg", 72.5, "Weight 72.5 kg", "weight 72.5 kilo hai", "वज़न 72.5 किलो है"),
        ("workout_min", 45, "45 minute workout done", "45 minute workout kiya", "45 मिनट वर्कआउट किया"),
        ("mood", 4, "Feeling pretty good today, 4 out of 5", "aaj mood 4 out of 5", "आज मूड 5 में से 4"),
    ])
    key, value = m[0], m[1]
    text = L(lang, m[2:])
    return text, dict(intent="capture", domain="health", kind=None, tool="log_metric",
                      urgency="low", entities={"metric": key, "value": value})


MISC = [
    ("list", "Add Sapiens to my books to read", "Sapiens ko padhne wali books mein daal do",
     "सेपियन्स को पढ़ने वाली किताबों में डाल दो"),
    ("purchase", "Need to buy a new phone charger", "naya phone charger kharidna hai", "नया फ़ोन चार्जर ख़रीदना है"),
    ("travel", "Goa trip from the 20th to the 23rd", "20 se 23 tak Goa trip hai", "20 से 23 तक गोवा ट्रिप है"),
    ("document", "Passport expires next March, renew it", "passport agle March expire ho raha hai, renew karna hai",
     "पासपोर्ट अगले मार्च में ख़त्म हो रहा है, रिन्यू करना है"),
    ("note", "Wifi password for the new flat is on the router", "naye flat ka wifi password router pe likha hai",
     "नए फ़्लैट का वाई-फ़ाई पासवर्ड राउटर पर लिखा है"),
    ("list", "Gift ideas for Didi: a watch or a kurta", "Didi ke gift ke liye watch ya kurta",
     "दीदी के तोहफ़े के लिए घड़ी या कुर्ता"),
    ("list", "Movies to watch: Lagaan and Swades", "dekhne wali movies mein Lagaan aur Swades daal do",
     "देखने वाली फ़िल्मों में लगान और स्वदेस डाल दो"),
    ("purchase", "Order a new pressure cooker", "naya pressure cooker mangwana hai", "नया प्रेशर कुकर मँगवाना है"),
    ("travel", "Flight to Bangalore on the 12th, booking done", "12 ko Bangalore ki flight book ho gayi",
     "12 को बैंगलोर की फ़्लाइट बुक हो गई"),
    ("document", "Driving licence renewal is due in December", "driving licence December mein renew karna hai",
     "ड्राइविंग लाइसेंस दिसंबर में रिन्यू करना है"),
    ("note", "Parking spot at the office is B2-14", "office mein parking B2-14 pe hai",
     "ऑफ़िस में पार्किंग B2-14 पर है"),
    ("purchase", "Buy running shoes before the marathon", "marathon se pehle running shoes lene hain",
     "मैराथन से पहले दौड़ने वाले जूते लेने हैं"),
]


def gen_misc(rng, lang):
    kind, *texts = rng.choice(MISC)
    return L(lang, texts), dict(intent="capture", domain="misc", kind=kind, tool="add_item",
                                urgency="low", entities={})


def gen_contact(rng, lang):
    p = rng.choice(FAMILY + FRIENDS)
    name = person(lang, p)
    ch, text = rng.choice([
        ("call", {"english": f"Spoke to {name} on the phone", "hinglish": f"{name} se baat ho gayi",
                  "hindi": f"{name} से बात हो गई"}),
        ("meet", {"english": f"Met {name} today", "hinglish": f"aaj {name} se mila", "hindi": f"आज {name} से मिला"}),
        ("message", {"english": f"Texted {name}", "hinglish": f"{name} ko message kar diya",
                     "hindi": f"{name} को मैसेज कर दिया"}),
        ("video", {"english": f"Video call with {name} done", "hinglish": f"{name} ke saath video call ho gayi",
                   "hindi": f"{name} के साथ वीडियो कॉल हो गई"}),
    ])
    return text[lang], dict(intent="contact_log", domain="people", kind=None, tool="log_contact",
                            urgency="low", entities={"person": p[0], "channel": ch})


def gen_add_person(rng, lang):
    p = rng.choice(FAMILY + FRIENDS)
    n = rng.choice([2, 3, 7, 14, 30])
    name = person(lang, p)
    every = {2: ("every 2 days", "har 2 din", "हर 2 दिन"), 3: ("every 3 days", "har 3 din", "हर 3 दिन"),
             7: ("every week", "har hafte", "हर हफ़्ते"), 14: ("every two weeks", "har do hafte", "हर दो हफ़्ते"),
             30: ("once a month", "mahine mein ek baar", "महीने में एक बार")}[n]
    text = {"english": f"Call {name} {every[0]}", "hinglish": f"{name} ko {every[1]} call karna hai",
            "hindi": f"{name} को {every[2]} फ़ोन करना है"}[lang]
    return text, dict(intent="capture", domain="people", kind=None, tool="add_person",
                      urgency="low", entities={"person": p[0], "cadence_days": n})


REMEMBER = [
    ("I take my chai without sugar", "main chai bina cheeni ke peeta hoon", "मैं चाय बिना चीनी के पीता हूँ"),
    ("My anniversary is on 14 February", "meri anniversary 14 February ko hai", "मेरी सालगिरह 14 फ़रवरी को है"),
    ("I go to the gym on weekday mornings", "main weekdays mein subah gym jaata hoon",
     "मैं हफ़्ते के दिनों में सुबह जिम जाता हूँ"),
    ("Kabir is vegetarian", "Kabir vegetarian hai", "कबीर शाकाहारी है"),
    ("My manager's name is Anita", "mere manager ka naam Anita hai", "मेरे मैनेजर का नाम अनीता है"),
    ("I don't take meetings before 10", "main 10 baje se pehle meeting nahi leta",
     "मैं 10 बजे से पहले मीटिंग नहीं लेता"),
    ("I am allergic to peanuts", "mujhe moongphali se allergy hai", "मुझे मूँगफली से एलर्जी है"),
    ("My son's school is DPS Noida", "mere bete ka school DPS Noida hai", "मेरे बेटे का स्कूल डीपीएस नोएडा है"),
    ("I prefer calls in the evening", "mujhe shaam ko call karna pasand hai", "मुझे शाम को फ़ोन करना पसंद है"),
    ("My car number is DL 3C AB 1234", "meri gaadi ka number DL 3C AB 1234 hai",
     "मेरी गाड़ी का नंबर DL 3C AB 1234 है"),
    ("I'm trying to cut down on sugar", "main cheeni kam karne ki koshish kar raha hoon",
     "मैं चीनी कम करने की कोशिश कर रहा हूँ"),
    ("Meera's daughter is called Tara", "Meera ki beti ka naam Tara hai", "मीरा की बेटी का नाम तारा है"),
]


def gen_remember(rng, lang):
    fact = rng.choice(REMEMBER)
    lead = {"english": "Remember that ", "hinglish": "Yaad rakhna, ", "hindi": "याद रखना, "}[lang]
    body = L(lang, fact)
    if lang == "english":
        body = body[0].lower() + body[1:] if not body.startswith(("I ", "My", "Kabir")) else body
    return lead + body, dict(intent="remember", domain=None, kind=None, tool="remember",
                             urgency="low", entities={})


UPDATES = [
    ("money", "bill", "Paid the electricity bill", "bijli ka bill bhar diya", "बिजली का बिल भर दिया", "done"),
    ("money", "lent", "Kabir paid me back", "Kabir ne paise lauta diye", "कबीर ने पैसे लौटा दिए", "done"),
    ("task", "errand", "Picked up Maa's medicines", "Maa ki dawai le li", "माँ की दवाई ले ली", "done"),
    ("promise", "by_me", "Sent Ravi the deck", "Ravi ko deck bhej diya", "रवि को डेक भेज दिया", "done"),
    ("task", "admin", "Car insurance renewed", "car insurance renew ho gayi", "गाड़ी का बीमा रिन्यू हो गया", "done"),
    ("meeting", "work", "Cancel the design review", "design review cancel kar do", "डिज़ाइन रिव्यू कैंसिल कर दो", "dropped"),
    ("task", "todo", "Drop the train tickets task, plans changed", "train tickets wala kaam chhod do, plan badal gaya",
     "ट्रेन टिकट वाला काम छोड़ दो, प्लान बदल गया", "dropped"),
    ("promise", "to_me", "Anita returned my book", "Anita ne meri book lauta di", "अनीता ने मेरी किताब लौटा दी", "done"),
    ("money", "borrowed", "Paid Meera back for lunch", "Meera ko lunch ke paise de diye", "मीरा को लंच के पैसे दे दिए", "done"),
    ("money", "bill", "Credit card bill is paid", "credit card ka bill chuka diya", "क्रेडिट कार्ड का बिल चुका दिया", "done"),
    ("task", "call", "Called the plumber, done", "plumber ko call kar liya", "प्लंबर को फ़ोन कर लिया", "done"),
    ("task", "chore", "AC service is done", "AC ki service ho gayi", "एसी की सर्विस हो गई", "done"),
    ("work", "deliverable", "Submitted the Mehta proposal", "Mehta wala proposal bhej diya", "मेहता वाला प्रपोज़ल भेज दिया", "done"),
    ("health", "appointment", "Cancel the dentist appointment", "dentist ka appointment cancel kar do",
     "डेंटिस्ट का अपॉइंटमेंट कैंसिल कर दो", "dropped"),
    ("task", "admin", "ITR filed", "ITR file ho gaya", "आईटीआर फ़ाइल हो गया", "done"),
    ("idea", "someday", "Forget the Leh cycling idea", "Leh cycling wala idea chhod do", "लेह साइकिल वाला आइडिया छोड़ दो", "dropped"),
]


def gen_update(rng, lang):
    domain, kind, en, hl, hi, status = rng.choice(UPDATES)
    return L(lang, (en, hl, hi)), dict(intent="update", domain=domain, kind=kind, tool="update_item",
                                       urgency="low", entities={"status": status})


QUERIES = [
    ("money", "borrowed", "Who do I have to pay back this week?", "is hafte mujhe kise paise lautane hain?",
     "इस हफ़्ते मुझे किसे पैसे लौटाने हैं?"),
    ("money", "lent", "Who owes me money?", "kis kis ne mujhse paise liye hain?", "किसने मुझसे पैसे लिए हैं?"),
    ("task", None, "What's due today?", "aaj kya kya karna hai?", "आज क्या-क्या करना है?"),
    ("meeting", None, "What meetings do I have tomorrow?", "kal kaun si meetings hain?", "कल कौन सी मीटिंग हैं?"),
    ("promise", "by_me", "What did I promise this week?", "is hafte maine kya promise kiya tha?",
     "इस हफ़्ते मैंने क्या वादा किया था?"),
    ("people", None, "Who haven't I spoken to in a while?", "kisse kaafi time se baat nahi hui?",
     "किससे काफ़ी समय से बात नहीं हुई?"),
    ("task", None, "What's overdue?", "kya kya overdue hai?", "क्या-क्या बाक़ी रह गया है?"),
    ("idea", None, "Show me my ideas", "mere saare ideas dikhao", "मेरे सारे आइडिया दिखाओ"),
    ("money", "bill", "Which bills are due this week?", "is hafte kaun se bills bharne hain?", "इस हफ़्ते कौन से बिल भरने हैं?"),
    ("promise", "to_me", "What are people supposed to give me?", "logon ne mujhe kya kya dena hai?",
     "लोगों ने मुझे क्या-क्या देना है?"),
    ("people", None, "Whose birthday is coming up?", "kiska birthday aane wala hai?", "किसका जन्मदिन आने वाला है?"),
    ("meeting", None, "When is my next meeting?", "meri agli meeting kab hai?", "मेरी अगली मीटिंग कब है?"),
    ("work", None, "How are my projects going?", "mere projects ka kya haal hai?", "मेरे प्रोजेक्ट्स का क्या हाल है?"),
    ("task", None, "What's on my plate tomorrow?", "kal ka kya scene hai?", "कल क्या-क्या है?"),
    ("money", None, "What's my net balance?", "mera net balance kitna hai?", "मेरा कुल हिसाब कितना है?"),
    ("misc", None, "Show my shopping list", "meri shopping list dikhao", "मेरी ख़रीदारी की लिस्ट दिखाओ"),
]


def gen_query(rng, lang):
    domain, kind, *texts = rng.choice(QUERIES)
    return L(lang, texts), dict(intent="query", domain=domain, kind=kind, tool="find_items",
                                needs_llm=False, urgency="low", entities={})


CHAT = [
    ("How are you, DONK?", "kaise ho DONK?", "कैसे हो डोंक?"),
    ("Tell me a joke", "ek joke sunao", "एक चुटकुला सुनाओ"),
    ("Give me some motivation for today", "aaj ke liye thoda motivation do", "आज के लिए थोड़ा हौसला दो"),
    ("What should I cook for dinner?", "dinner mein kya banaun?", "रात के खाने में क्या बनाऊँ?"),
    ("Thanks DONK", "thank you DONK", "धन्यवाद डोंक"),
    ("What can you do?", "tum kya kya kar sakte ho?", "तुम क्या-क्या कर सकते हो?"),
    ("I'm feeling a bit low today", "aaj thoda udaas lag raha hai", "आज थोड़ा उदास लग रहा है"),
    ("Explain compound interest simply", "compound interest simple mein samjhao", "चक्रवृद्धि ब्याज आसान भाषा में समझाओ"),
    ("Good morning!", "good morning DONK", "सुप्रभात डोंक"),
    ("Write a birthday wish for Papa", "Papa ke liye birthday wish likh do", "पापा के लिए जन्मदिन की शुभकामना लिख दो"),
]


def gen_chat(rng, lang):
    return L(lang, rng.choice(CHAT)), dict(intent="chat", domain=None, kind=None, tool="none",
                                           needs_llm=True, urgency="low", entities={})


MULTI = [
    ("Plan my day and remind me that it's Arjun's birthday",
     "aaj ka plan bana do aur yaad dilana ki Arjun ka birthday hai",
     "आज का प्लान बना दो और याद दिलाना कि अर्जुन का जन्मदिन है", "other", None),
    ("Lent Kabir 2000 and I have to call Maa tonight",
     "Kabir ko 2000 diye aur raat ko Maa ko call karna hai",
     "कबीर को 2000 दिए और रात को माँ को फ़ोन करना है", "capture", "money"),
    ("Move all my meetings tomorrow to the afternoon",
     "kal ki saari meetings dopahar mein shift kar do",
     "कल की सारी मीटिंग दोपहर में कर दो", "update", "meeting"),
    ("Something about the thing with Ravi, sort it out",
     "Ravi wala woh kaam, dekh lena", "रवि वाला वो काम, देख लेना", "other", None),
    ("How did I sleep this week compared to last week?",
     "is hafte ki neend pichhle hafte se kaisi rahi?",
     "इस हफ़्ते की नींद पिछले हफ़्ते से कैसी रही?", "query", "health"),
    ("Suggest what I should focus on this weekend",
     "is weekend kis cheez pe focus karun?", "इस वीकेंड किस चीज़ पर ध्यान दूँ?", "chat", None),
    ("Delete all the done tasks", "saare done tasks delete kar do", "सारे पूरे हुए काम हटा दो", "update", "task"),
    ("Remind me before Dadi's birthday and buy a gift",
     "Dadi ke birthday se pehle yaad dilana aur gift lena hai",
     "दादी के जन्मदिन से पहले याद दिलाना और तोहफ़ा लेना है", "capture", "people"),
    ("Meera paid me back and I paid the rent", "Meera ne paise lauta diye aur maine rent de diya",
     "मीरा ने पैसे लौटा दिए और मैंने किराया दे दिया", "update", "money"),
    ("Push everything from today to tomorrow", "aaj ka sab kuch kal pe daal do", "आज का सब कुछ कल पर डाल दो",
     "update", "task"),
    ("Do the usual for Sunday", "Sunday ke liye wahi jo hamesha", "रविवार के लिए वही जो हमेशा", "other", None),
    ("Compare my spending on bills this month and last month",
     "is mahine aur pichhle mahine ke bills compare karo",
     "इस महीने और पिछले महीने के बिलों की तुलना करो", "query", "money"),
    ("Add a meeting with Ravi and Anita on Friday and send them the agenda",
     "Friday ko Ravi aur Anita ke saath meeting rakho aur agenda bhej do",
     "शुक्रवार को रवि और अनीता के साथ मीटिंग रखो और एजेंडा भेज दो", "capture", "meeting"),
    ("Make a packing list for Goa", "Goa ke liye packing list bana do", "गोवा के लिए पैकिंग लिस्ट बना दो",
     "other", "misc"),
    ("Which promises am I about to break?", "kaun se promise toot ne wale hain?",
     "कौन से वादे टूटने वाले हैं?", "query", "promise"),
    ("That thing I said yesterday, change it to Thursday", "kal jo bola tha usko Thursday kar do",
     "कल जो बोला था उसको गुरुवार कर दो", "update", None),
]


def gen_multi(rng, lang):
    *texts, intent, domain = rng.choice(MULTI)
    return L(lang, texts), dict(intent=intent, domain=domain, kind=None, tool="none",
                                needs_llm=True, urgency="medium", entities={}, tags=["multi_or_vague"])


CATEGORIES = [  # (name, generator, count)
    ("task", gen_task, 60), ("meeting", gen_meeting, 35), ("money", gen_money, 55),
    ("promise", gen_promise, 35), ("idea", gen_idea, 20), ("work", gen_work, 15),
    ("health", gen_health, 20), ("metric", gen_metric, 15), ("misc", gen_misc, 15),
    ("contact", gen_contact, 25), ("add_person", gen_add_person, 15), ("remember", gen_remember, 15),
    ("update", gen_update, 20), ("query", gen_query, 25), ("chat", gen_chat, 10), ("multi", gen_multi, 20),
]


def main() -> None:
    rng = random.Random(SEED)
    total = sum(c for _, _, c in CATEGORIES)
    assert total == sum(LANG_QUOTA.values()), total
    langs = [lang for lang, n in LANG_QUOTA.items() for _ in range(n)]
    rng.shuffle(langs)

    rows, seen = [], set()
    for name, gen, count in CATEGORIES:
        made = 0
        while made < count:
            lang = langs[len(rows)]
            for _ in range(200):
                text, labels = gen(rng, lang)
                text = " ".join(text.split())
                if text not in seen:
                    break
            else:
                raise RuntimeError(f"could not make a unique {name} utterance in {lang}")
            seen.add(text)
            row = {"id": f"e{len(rows) + 1:04d}", "lang": lang, "category": name, "text": text,
                   "intent": labels["intent"], "domain": labels.get("domain"), "kind": labels.get("kind"),
                   "tool": labels["tool"], "needs_llm": labels.get("needs_llm", False),
                   "urgency": labels["urgency"], "entities": labels.get("entities", {})}
            if labels.get("tags"):
                row["tags"] = labels["tags"]
            rows.append(row)
            made += 1

    # Stratified 70/30 split by (category, lang).
    strata = defaultdict(list)
    for row in rows:
        strata[(row["category"], row["lang"])].append(row)
    for group in strata.values():
        rng.shuffle(group)
        n_test = round(len(group) * 0.3)
        for i, row in enumerate(group):
            row["split"] = "test" if i < n_test else "train"

    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"_meta": {"ref_time": REF_TIME, "seed": SEED, "count": len(rows)}}) + "\n")
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"wrote {len(rows)} utterances to {OUT}")
    print("lang:", dict(Counter(r["lang"] for r in rows)))
    print("split:", dict(Counter(r["split"] for r in rows)))
    print("tool:", dict(Counter(r["tool"] for r in rows)))
    print("needs_llm:", dict(Counter(r["needs_llm"] for r in rows)))


if __name__ == "__main__":
    main()
