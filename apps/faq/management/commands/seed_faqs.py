from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.faq.models import FAQ, FAQCategory


CATEGORIES = [
    ("education", "Education Services", "Ayyukan Ilimi", "Scholarships, admissions, grants and examinations.", "Tallafin karatu, shiga makaranta, gudummawa da jarabawa.", "bi-mortarboard", 10),
    ("healthcare", "Healthcare Services", "Ayyukan Lafiya", "Health facilities, insurance and family healthcare.", "Asibitoci, inshorar lafiya da lafiyar iyali.", "bi-heart-pulse", 20),
    ("agriculture", "Agriculture", "Noma", "Farmer services, inputs and extension support.", "Ayyukan manoma, kayan noma da shawarwarin noma.", "bi-tree", 30),
    ("business-investment", "Business and Investment", "Kasuwanci da Zuba Jari", "Business premises, SMEs and investment guidance.", "Wuraren kasuwanci, ƙananan sana’o’i da zuba jari.", "bi-shop", 40),
    ("civil-registration", "Civil Registration and Documentation", "Rajista da Takardun Shaida", "Birth, death and official record guidance.", "Haihuwa, mutuwa da takardun hukuma.", "bi-file-earmark-text", 50),
    ("tax-revenue", "Tax and Revenue", "Haraji da Kuɗaɗen Shiga", "Taxpayer registration, bills, payments and receipts.", "Rajistar mai biyan haraji, kuɗi, biyan haraji da rasit.", "bi-receipt", 60),
    ("employment-youth", "Employment and Youth Empowerment", "Ayyukan Yi da Tallafin Matasa", "Official vacancies, skills and youth programmes.", "Guraben aiki, koyon sana’a da shirye-shiryen matasa.", "bi-briefcase", 70),
    ("government-administration", "Government Administration", "Gudanarwar Gwamnati", "Ministries, local offices, contacts and enquiries.", "Ma’aikatu, ƙananan hukumomi, tuntuɓa da korafe-korafe.", "bi-bank", 80),
]

FAQS = [
    {
        "category": "education",
        "question_en": "How can I apply for a Nasarawa State scholarship or bursary?",
        "answer_en": "Applications are accepted only when the Nasarawa State Scholarship Board opens an application round. Check the Board portal for a current notice, eligibility rules, required documents and closing date. Do not rely on an old social-media announcement.",
        "question_ha": "Ta yaya zan nemi tallafin karatu ko bursary na Jihar Nasarawa?",
        "answer_ha": "Ana karɓar buƙata ne idan Hukumar Tallafin Karatu ta Jihar Nasarawa ta buɗe sabon zagaye. Duba shafin Hukumar domin sanarwar yanzu, sharuddan cancanta, takardun da ake buƙata da ranar rufewa. Kada ka dogara da tsohuwar sanarwa a kafar sada zumunta.",
        "keywords_en": ["scholarship", "bursary", "student grant", "scholarship board"],
        "keywords_ha": ["tallafin karatu", "bursary", "dalibi", "tallafin dalibi"],
        "alternative_questions_en": ["Where is the scholarship application?", "Is the state bursary open?"],
        "alternative_questions_ha": ["A ina ake neman bursary?", "An bude tallafin karatu?"],
        "source_name": "Nasarawa State Scholarship Board Portal",
        "source_url": "https://nassb-portal.org.ng",
        "featured": True,
    },
    {
        "category": "education",
        "question_en": "What are the current requirements for admission to a state school?",
        "answer_en": "A single statewide admissions checklist has not yet been confirmed for this knowledge base. Requirements differ by school and level. Confirm the current form, documents, dates and any approved charges directly with the named school or the responsible education authority before applying.",
        "question_ha": "Mene ne sharuddan shiga makarantar jihar a yanzu?",
        "answer_ha": "Har yanzu ba a tabbatar da jerin sharuddan shiga dukkan makarantun jihar a wannan kundin ba. Sharudda suna bambanta bisa makaranta da matakin karatu. Ka tabbatar da fom, takardu, ranaku da kuɗin da aka amince da su kai tsaye daga makarantar ko hukumar ilimi kafin nema.",
        "keywords_en": ["school admission", "registration", "admission requirements"],
        "keywords_ha": ["shiga makaranta", "rajistar makaranta", "sharuddan shiga"],
        "source_name": "Nasarawa State Ministry of Education",
        "source_url": "https://nasarawastate.gov.ng/education",
        "awaiting": True,
    },
    {
        "category": "healthcare",
        "question_en": "How do I enrol for Nasarawa State health insurance?",
        "answer_en": "The Nasarawa State Health Insurance Agency manages state health-insurance programmes. Start with the NASHIA portal and confirm the plan, current contribution, approved facility and activation process directly with the Agency before making a payment.",
        "question_ha": "Ta yaya zan yi rajistar inshorar lafiya ta Jihar Nasarawa?",
        "answer_ha": "Hukumar Inshorar Lafiya ta Jihar Nasarawa ce ke kula da shirye-shiryen inshora. Ka fara da shafin NASHIA, sannan ka tabbatar da tsarin inshora, kuɗin yanzu, asibitin da aka amince da shi da yadda ake kunna inshorar daga Hukumar kafin biya.",
        "keywords_en": ["health insurance", "NASHIA", "medical cover", "enrol health"],
        "keywords_ha": ["inshorar lafiya", "NASHIA", "rajistar lafiya", "asibiti"],
        "source_name": "NASHIA Enrolment Portal",
        "source_url": "https://www.nashiaportal.org",
        "featured": True,
    },
    {
        "category": "healthcare",
        "question_en": "Where is the nearest government hospital or primary healthcare centre?",
        "answer_en": "A verified, complete facility directory is not yet available in this knowledge base. Use the official government contact channel to request the current facility serving your ward or community. For an immediate emergency, call 112; this chatbot cannot dispatch help.",
        "question_ha": "Ina asibitin gwamnati ko cibiyar lafiya mafi kusa?",
        "answer_ha": "Har yanzu babu cikakken jerin cibiyoyin lafiya da aka tabbatar a wannan kundin. Yi amfani da hanyar tuntuɓar gwamnati ta hukuma domin neman cibiyar da ke kula da ward ko al’ummarka. Idan gaggawa ce, kira 112; wannan manhaja ba za ta iya tura jami’an agaji ba.",
        "keywords_en": ["government hospital", "primary healthcare", "PHC", "nearest clinic"],
        "keywords_ha": ["asibitin gwamnati", "cibiyar lafiya", "asibiti mafi kusa"],
        "source_name": "Nasarawa State Official Contacts",
        "source_url": "https://nasarawastate.gov.ng/contacts",
        "awaiting": True,
    },
    {
        "category": "agriculture",
        "question_en": "How can farmers find current state agricultural support programmes?",
        "answer_en": "Farm inputs, assets and livelihood programmes are announced when registration or beneficiary selection opens. Check dated Nasarawa State project notices and the responsible local agriculture office. Registration does not guarantee selection, and you should never pay an individual to add your name to a beneficiary list.",
        "question_ha": "Ta yaya manoma za su samu shirye-shiryen tallafin noma na jihar?",
        "answer_ha": "Ana sanar da kayan noma, kadarori da tallafin rayuwa idan an buɗe rajista ko zaɓen masu amfana. Duba sanarwar ayyukan Jihar Nasarawa mai kwanan wata da ofishin noma na yankinka. Rajista ba ta tabbatar da zaɓe ba, kuma kada ka biya mutum domin saka sunanka a jerin masu amfana.",
        "keywords_en": ["farmer support", "farm inputs", "fertilizer", "agricultural grant", "tractor"],
        "keywords_ha": ["tallafin manoma", "kayan noma", "taki", "tallafin noma", "tarakta"],
        "source_name": "Nasarawa State Project Notices",
        "source_url": "https://nasarawastate.gov.ng/category/projects/ongoing-projects",
        "featured": True,
    },
    {
        "category": "agriculture",
        "question_en": "How do I register as a farmer in Nasarawa State?",
        "answer_en": "The current statewide farmer-registration channel and document checklist are awaiting confirmation by the responsible agriculture authority. Do not submit personal records or pay a registration agent until a dated official notice identifies the approved process.",
        "question_ha": "Ta yaya zan yi rajista a matsayin manomi a Jihar Nasarawa?",
        "answer_ha": "Ana jiran hukumar noma ta tabbatar da hanyar rajistar manoma ta jihar da jerin takardun da ake buƙata. Kada ka miƙa takardun sirri ko ka biya dillalin rajista sai sanarwa mai kwanan wata daga hukuma ta bayyana hanyar da aka amince da ita.",
        "keywords_en": ["farmer registration", "register farmer", "farmer database"],
        "keywords_ha": ["rajistar manomi", "rajistar manoma", "sunan manomi"],
        "awaiting": True,
    },
    {
        "category": "business-investment",
        "question_en": "How do I register a business premises in Nasarawa State?",
        "answer_en": "The State Ministry of Trade, Industry and Investment handles business-premises registration. Create an account on its premises-registration portal, provide the requested premises and business documents, pay only an official assessment and download the certificate after approval. This state process is separate from registering a company or business name with the federal Corporate Affairs Commission.",
        "question_ha": "Ta yaya zan yi rajistar wurin kasuwanci a Jihar Nasarawa?",
        "answer_ha": "Ma’aikatar Ciniki, Masana’antu da Zuba Jari ta jihar ce ke rajistar wuraren kasuwanci. Ƙirƙiri asusu a shafinta, bayar da bayanan wurin da takardun da aka nema, biya kuɗin hukuma kawai, sannan ka sauke takardar shaida bayan an amince. Wannan ya bambanta da rajistar kamfani ko sunan kasuwanci a CAC ta tarayya.",
        "keywords_en": ["business premises", "register shop", "business permit", "premises certificate"],
        "keywords_ha": ["wurin kasuwanci", "rajistar shago", "izinin kasuwanci", "takardar kasuwanci"],
        "source_name": "Ministry of Trade Business Premises Portal",
        "source_url": "https://www.mtiinasarawa.com.ng/registration/business-premises",
        "featured": True,
    },
    {
        "category": "business-investment",
        "question_en": "Are there current government grants or loans for SMEs?",
        "answer_en": "No current SME grant or loan application has been confirmed for this knowledge base. Apply only through a dated notice published by the responsible government agency. Do not pay anyone who promises selection or asks for a personal-bank transfer.",
        "question_ha": "Akwai tallafin gwamnati ko rance ga ƙananan kasuwanci a yanzu?",
        "answer_ha": "Ba a tabbatar da wani shirin tallafi ko rance ga ƙananan kasuwanci a wannan kundin yanzu ba. Ka nema ne kawai ta sanarwa mai kwanan wata daga hukumar gwamnati da ke da alhaki. Kada ka biya mai alkawarin zaɓe ko mai neman tura kuɗi zuwa asusun mutum.",
        "keywords_en": ["SME grant", "business loan", "government grant", "small business support"],
        "keywords_ha": ["tallafin kasuwanci", "rance", "kananan kasuwanci", "tallafin gwamnati"],
        "awaiting": True,
    },
    {
        "category": "civil-registration",
        "question_en": "Where can I register a birth or request a birth certificate?",
        "answer_en": "Birth registration is handled by Nigeria’s National Population Commission, not by a Nasarawa State ministry. Follow the current NPC guidance or visit an NPC registration centre. Requirements can differ for a newborn, late registration or re-issuance, so request the checklist for your case directly from NPC.",
        "question_ha": "A ina zan yi rajistar haihuwa ko neman takardar shaidar haihuwa?",
        "answer_ha": "Hukumar Ƙidaya ta Ƙasa (NPC) ce ke rajistar haihuwa, ba ma’aikatar Jihar Nasarawa ba. Bi umarnin NPC na yanzu ko je cibiyar rajistar NPC. Takardun jariri, jinkirin rajista ko sake fitar da takarda suna iya bambanta, saboda haka nemi jerin da ya dace daga NPC.",
        "keywords_en": ["birth certificate", "birth registration", "new baby", "NPC"],
        "keywords_ha": ["takardar haihuwa", "rajistar haihuwa", "jariri", "NPC"],
        "source_name": "National Population Commission",
        "source_url": "https://nationalpopulation.gov.ng",
        "featured": True,
    },
    {
        "category": "civil-registration",
        "question_en": "How do I register a death or obtain an official death record?",
        "answer_en": "The precise local registration point and document checklist have not yet been confirmed for this knowledge base. Death registration is a civil-registration matter; request the current procedure from the National Population Commission before submitting documents or paying any charge.",
        "question_ha": "Ta yaya zan yi rajistar mutuwa ko samun takardar mutuwa ta hukuma?",
        "answer_ha": "Har yanzu ba a tabbatar da cibiyar rajista da takardun da ake buƙata a wannan kundin ba. Rajistar mutuwa tana cikin rajistar jama’a; nemi hanyar yanzu daga Hukumar Ƙidaya ta Ƙasa kafin miƙa takardu ko biyan kuɗi.",
        "keywords_en": ["death registration", "death certificate", "official death record"],
        "keywords_ha": ["rajistar mutuwa", "takardar mutuwa", "shaidar mutuwa"],
        "source_name": "National Population Commission",
        "source_url": "https://nationalpopulation.gov.ng",
        "awaiting": True,
    },
    {
        "category": "tax-revenue",
        "question_en": "How can I pay a Nasarawa State tax or government bill?",
        "answer_en": "Use the Nasarawa State central billing portal to generate an official invoice. Select the relevant tax or service, confirm the payer details, pay online or use the invoice at an approved bank, and retain the receipt. Do not pay a state bill into a personal bank account.",
        "question_ha": "Ta yaya zan biya harajin Jihar Nasarawa ko kuɗin gwamnati?",
        "answer_ha": "Yi amfani da shafin biyan kuɗi na Jihar Nasarawa domin samar da takardar biyan kuɗi ta hukuma. Zaɓi haraji ko aikin, tabbatar da bayanan mai biya, biya ta intanet ko da takardar a bankin da aka amince, sannan ka ajiye rasit. Kada ka biya kuɗin jihar zuwa asusun mutum.",
        "keywords_en": ["pay tax", "tax payment", "government bill", "invoice", "IGR", "receipt"],
        "keywords_ha": ["biya haraji", "biyan haraji", "kudin gwamnati", "takardar biya", "rasit"],
        "alternative_questions_en": ["Where do I generate a tax invoice?", "How do I pay state revenue?"],
        "alternative_questions_ha": ["A ina zan samu takardar biyan haraji?", "Yaya ake biyan kudin shiga na jihar?"],
        "source_name": "Nasarawa Central Billing Portal",
        "source_url": "https://nasarawaigr.com",
        "featured": True,
    },
    {
        "category": "tax-revenue",
        "question_en": "How do I get help with taxpayer registration or my tax account?",
        "answer_en": "Start on the central billing portal as an individual or organisation. For an account, assessment or receipt problem, use the Nasarawa State Internal Revenue Service official contact page or visit Revenue House, Lafia during its published working hours. Do not send a password or card PIN by email or chat.",
        "question_ha": "Ta yaya zan samu taimako kan rajistar mai biyan haraji ko asusun haraji?",
        "answer_ha": "Ka fara a shafin biyan kuɗi a matsayin mutum ko kamfani. Don matsalar asusu, lissafin haraji ko rasit, yi amfani da shafin tuntuɓar Hukumar Haraji ta Jihar Nasarawa ko je Revenue House, Lafia a lokutan aikin da aka wallafa. Kada ka aika kalmar sirri ko PIN ta imel ko chat.",
        "keywords_en": ["taxpayer registration", "tax account", "tax ID", "TIN", "NSIRS"],
        "keywords_ha": ["rajistar mai biyan haraji", "asusun haraji", "lambar haraji", "NSIRS"],
        "source_name": "Nasarawa State Internal Revenue Service",
        "source_url": "https://www.irs.na.gov.ng",
    },
    {
        "category": "employment-youth",
        "question_en": "Where can I find Nasarawa State government job vacancies?",
        "answer_en": "Check recruitment notices published by the Nasarawa State Government and the relevant commission or agency. Vacancies are not continuously open, so apply only when a dated official notice is active and use only the application link named in that notice. Be cautious of anyone requesting payment or promising an appointment.",
        "question_ha": "A ina zan samu guraben aikin gwamnati na Jihar Nasarawa?",
        "answer_ha": "Duba sanarwar ɗaukar ma’aikata da Gwamnatin Jihar Nasarawa ko hukumar da ta dace ta wallafa. Ba kullum ake buɗe guraben aiki ba; ka nema ne idan sanarwa mai kwanan wata tana aiki, kuma ka yi amfani da hanyar da sanarwar ta bayar kawai. Yi hankali da mai neman kuɗi ko alkawarin ba ka aiki.",
        "keywords_en": ["government job", "civil service", "vacancy", "recruitment", "employment"],
        "keywords_ha": ["aikin gwamnati", "gurbin aiki", "daukar maaikata", "neman aiki"],
        "source_name": "Nasarawa State Recruitment Notices",
        "source_url": "https://nasarawastate.gov.ng/recruitment",
        "featured": True,
    },
    {
        "category": "employment-youth",
        "question_en": "How can I apply for a youth empowerment or skills programme?",
        "answer_en": "No currently open statewide youth or skills application has been confirmed for this knowledge base. Wait for a dated notice from the responsible state agency, verify its application domain and closing date, and never pay an individual to secure a place.",
        "question_ha": "Ta yaya zan nemi shirin tallafin matasa ko koyon sana’a?",
        "answer_ha": "Ba a tabbatar da wani buɗaɗɗen shirin matasa ko koyon sana’a na jihar a wannan kundin yanzu ba. Jira sanarwa mai kwanan wata daga hukumar da ke da alhaki, tabbatar da shafin nema da ranar rufewa, kuma kada ka biya mutum domin samun gurbi.",
        "keywords_en": ["youth empowerment", "skills acquisition", "internship", "youth programme"],
        "keywords_ha": ["tallafin matasa", "koyon sanaa", "horon aiki", "shirin matasa"],
        "awaiting": True,
    },
    {
        "category": "government-administration",
        "question_en": "How can I contact the Nasarawa State Government or make an enquiry?",
        "answer_en": "Use the official government contacts page for a general enquiry or to identify the responsible ministry, department or agency. State the service and location involved and include an application or invoice reference if available. Do not send a password, card PIN or other secret credential.",
        "question_ha": "Ta yaya zan tuntuɓi Gwamnatin Jihar Nasarawa ko yin tambaya?",
        "answer_ha": "Yi amfani da shafin tuntuɓar gwamnati na hukuma domin tambaya ko gano ma’aikata, sashe ko hukumar da ta dace. Faɗi aikin da wurin da batun ya shafa, sannan ka saka lambar buƙata ko takardar biya idan kana da ita. Kada ka aika kalmar sirri, PIN ko wasu bayanan sirri.",
        "keywords_en": ["contact government", "government enquiry", "complaint", "government email", "help desk"],
        "keywords_ha": ["tuntubi gwamnati", "tambayar gwamnati", "korafi", "imel", "neman taimako"],
        "source_name": "Official Nasarawa State Contacts",
        "source_url": "https://nasarawastate.gov.ng/contacts",
        "featured": True,
    },
    {
        "category": "government-administration",
        "question_en": "What are the 13 local government areas in Nasarawa State?",
        "answer_en": "Nasarawa State has 13 local government areas: Akwanga, Awe, Doma, Karu, Keana, Keffi, Kokona, Lafia, Nasarawa, Nasarawa Eggon, Obi, Toto and Wamba.",
        "question_ha": "Waɗanne ƙananan hukumomi 13 ne a Jihar Nasarawa?",
        "answer_ha": "Jihar Nasarawa tana da ƙananan hukumomi 13: Akwanga, Awe, Doma, Karu, Keana, Keffi, Kokona, Lafia, Nasarawa, Nasarawa Eggon, Obi, Toto da Wamba.",
        "keywords_en": ["local government", "LGA", "13 LGAs", "local council"],
        "keywords_ha": ["kananan hukumomi", "karamar hukuma", "LGA", "hukumomi 13"],
        "source_name": "Official Nasarawa State Website",
        "source_url": "https://nasarawastate.gov.ng",
    },
]


class Command(BaseCommand):
    help = "Create the required bilingual categories and reviewed starter FAQs idempotently."

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for slug, name_en, name_ha, description_en, description_ha, icon, order in CATEGORIES:
            category, _ = FAQCategory.objects.update_or_create(
                slug=slug,
                defaults={
                    "name_en": name_en,
                    "name_ha": name_ha,
                    "description_en": description_en,
                    "description_ha": description_ha,
                    "icon": icon,
                    "display_order": order,
                    "is_active": True,
                },
            )
            categories[slug] = category

        created = updated = 0
        for data in FAQS:
            category = categories[data["category"]]
            awaiting = data.get("awaiting", False)
            defaults = {
                "category": category,
                "answer_en": data["answer_en"],
                "question_ha": data["question_ha"],
                "answer_ha": data["answer_ha"],
                "keywords_en": data.get("keywords_en", []),
                "keywords_ha": data.get("keywords_ha", []),
                "alternative_questions_en": data.get("alternative_questions_en", []),
                "alternative_questions_ha": data.get("alternative_questions_ha", []),
                "status": FAQ.Status.PUBLISHED,
                "verification_status": FAQ.VerificationStatus.AWAITING if awaiting else FAQ.VerificationStatus.VERIFIED,
                "source_name": data.get("source_name", ""),
                "source_url": data.get("source_url", ""),
                "last_verified_at": None if awaiting else date(2026, 11, 5),
                "is_featured": data.get("featured", False),
            }
            faq, was_created = FAQ.objects.update_or_create(
                question_en=data["question_en"], defaults=defaults
            )
            faq.full_clean()
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(categories)} categories and {len(FAQS)} FAQs "
                f"({created} created, {updated} updated)."
            )
        )
