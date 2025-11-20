from flask import Flask, render_template_string, request, jsonify
import csv
import os
import json
import pandas as pd
from Emsi import extract_skills_from_text  # <-- تفترض إنه موجود عندك

app = Flask(__name__)
esco_df = pd.read_excel("esco.xlsx")
titles_list = esco_df['Title'].dropna().tolist()
# ==============================
# Load skills CSV
# ==============================
def load_skills_csv(path):
    skills_list = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"Skills CSV not found at: {path}")
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # تأكد من وجود المفاتيح المتوقعة في ال CSV
            skills_list.append({
                'name': row.get('name', '').strip(),
                'category_name': row.get('category_name', '').strip(),
                'subcategory_name': row.get('subcategory_name', '').strip(),
                'type_name': row.get('type_name', '').strip()
            })
    return skills_list

# عدّل المسار حسب جهازك
SKILLS_CSV_PATH = "all_skills_latest.csv"
skills_list = load_skills_csv(SKILLS_CSV_PATH)

# تحضير قوائم فريدة للـ categories و subcategories لتمريرها للـ template
def unique_sorted(values):
    return sorted(list({v for v in values if v}))

categories = unique_sorted([s['category_name'] for s in skills_list])
subcategories = unique_sorted([s['subcategory_name'] for s in skills_list])

# ==============================
# HTML Template (single-file)
# ==============================
form_html = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Company Job Form</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f4f4f4; }
        .box { background: #fff; padding: 15px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 0 5px rgba(0,0,0,0.1); }
        h3 { margin-top: 0; font-family: 'Verdana', sans-serif; color: #333; }
        input, select, textarea, button { width: 100%; padding: 6px; margin: 5px 0 10px 0; box-sizing: border-box; font-family: 'Arial', sans-serif; }
        input[type="submit"] { width: auto; background: #007BFF; color: #fff; border: none; padding: 8px 16px; cursor: pointer; border-radius: 4px; font-size: 14px; }
        input[type="submit"]:hover { background: #0056b3; }
        pre { background: #eee; padding: 10px; border-radius: 6px; }
        .phone-wrapper { display: flex; gap: 5px; }
        .phone-wrapper select, .phone-wrapper input { flex: none; }
        .phone-wrapper .phone-code { width: 80px; }
        .phone-wrapper .phone-number { flex: 1; }
        .radio-group label { margin-right: 15px; }
        table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        td { padding: 5px; vertical-align: top; }
        /* small adjustments */
        #granulated_skill_dropdown { width: 100%; height: 140px; }
        #skill_search { width: 100%; padding: 6px; }
        .inline { display:inline-block; vertical-align:middle; }
        .muted { color:#666; font-size:13px; }
    </style>
</head>
<body>

<form method="POST">

<!-- =================== Basic Info Box =================== -->
<div class="box">
    <h3>Basic Info</h3>
    <label>1. Company Name</label>
    <input type="text" name="Company_Name" placeholder="ABC Technologies">
    
    <label>2. Company Website</label>
    <input type="url" name="Company_Website" placeholder="https://company.com/jobs/12345">
    
    <label>3. Contact Person</label>
    <input type="text" name="Contact_Person" placeholder="Contact person name">
    
    <label>4. Email</label>
    <input type="email" name="Email" placeholder="example@company.com">
    
    <style>
    /* Optional: make the select box a bit wider than default */
    .phone-wrapper .select2-container {
        width: 150px !important; /* Adjust width as needed */
    }
    </style>

    <label>5. Phone Number</label>
    <div class="phone-wrapper" style="display: flex; gap: 10px;">
         <select class="phone-code" name="Phone_Code" id="phone-code" required style="width: 150px;">
            <option value="">Select country code</option>
        </select>
        <input type="text" class="phone-number"
       placeholder="Enter phone number"
       pattern="^\\d{6,15}$" required>
    </div>

    <!-- Select2 for searchable dropdown -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/select2/4.1.0-rc.0/css/select2.min.css" rel="stylesheet" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/select2/4.1.0-rc.0/js/select2.min.js"></script>

    <script>
    fetch('countries_codes_iso3.json')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('phone-code');

            data.forEach(country => {
                const option = document.createElement('option');
                option.value = `+${country.code}`;
                option.textContent = `${country.iso3} +${country.code}`; // ISO3 first
                option.setAttribute('data-iso3', country.iso3);

                if (country.iso3 === 'LBN') {
                    option.selected = true; // default Lebanon
                }

                select.appendChild(option);
            });

            // Initialize Select2 for search
            $('#phone-code').select2({
                placeholder: "Select country code",
                allowClear: true,
                width: '150px' // increase width here as well
            });
        })
        .catch(err => console.error('Error loading JSON:', err));
    </script>
    
    
    <label>6. Company Size (number of employees)</label>
    <input type="text" name="Company_Size" placeholder="e.g., 50–200">
    
    <label>7. Industry</label>
    <select id="industry_section" name="Industry" style="width: 100%;">
        <option value="">-- Select Industry --</option>
        <option value="Activities of extraterritorial organizations and bodies">Activities of extraterritorial organizations and bodies</option>
        <option value="Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use">Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use</option>
        <option value="Accommodation and food service activities">Accommodation and food service activities</option>
        <option value="Administrative and support service activities">Administrative and support service activities</option>
        <option value="Agriculture, forestry and fishing">Agriculture, forestry and fishing</option>
        <option value="Arts, entertainment and recreation">Arts, entertainment and recreation</option>
        <option value="Construction">Construction</option>
        <option value="Education">Education</option>
        <option value="Electricity, gas, steam and air conditioning supply">Electricity, gas, steam and air conditioning supply</option>
        <option value="Financial and insurance activities">Financial and insurance activities</option>
        <option value="Human health and social work activities">Human health and social work activities</option>
        <option value="Information and communication">Information and communication</option>
        <option value="Manufacturing">Manufacturing</option>
        <option value="Mining and quarrying">Mining and quarrying</option>
        <option value="Other service activities">Other service activities</option>
        <option value="Professional, scientific and technical activities">Professional, scientific and technical activities</option>
        <option value="Public administration and defense; compulsory social security">Public administration and defense; compulsory social security</option>
        <option value="Real estate activities">Real estate activities</option>
        <option value="Transportation and storage">Transportation and storage</option>
        <option value="Water supply; sewerage, waste management and remediation activities">Water supply; sewerage, waste management and remediation activities</option>
        <option value="Wholesale and retail trade; repair of motor vehicles and motorcycles">Wholesale and retail trade; repair of motor vehicles and motorcycles</option>
        <option value="Others">Others</option>
    </select>
    <input type="text" id="other_industry" name="OtherIndustry" placeholder="Please specify" style="display:none; width:100%; margin-top:5px;"/>

    <script>
    const industrySelect = document.getElementById('industry_section');
    const otherInput = document.getElementById('other_industry');

    industrySelect.addEventListener('change', function() {
        if (this.value === 'Others') {
            otherInput.style.display = 'block';
        } else {
            otherInput.style.display = 'none';
            otherInput.value = ''; // clear previous input
        }
    });
    </script>
    
<label for="governorate">8. Governorate</label>
<select id="governorate">
    <option value="">Select Governorate</option>
    <option value="Akkar">Akkar</option>
    <option value="Baalbek-Hermel">Baalbek-Hermel</option>
    <option value="Bekaa">Bekaa</option>
    <option value="Beirut">Beirut</option>
    <option value="Mount Lebanon">Mount Lebanon</option>
    <option value="North Lebanon">North Lebanon</option>
    <option value="South Lebanon">South Lebanon</option>
    <option value="Nabatieh">Nabatieh</option>
</select>

<label for="city">9. City</label>
<select id="city">
    <option value="">Select City</option>
</select>
<input type="text" id="other_city" name="Other_City" placeholder="Please specify your city" style="display:none; width:100%; margin-top:5px;" />

<script>
// Hardcoded municipalities object
const municipalities = {
    "Akkar": ["Daghlah Ad Aakkar","Aidmoon-Shekhlar Aakkar","al-Dhahab Ain Aakkar","al-Zayt Ain Aakkar",
        "Yaaqub Ain Aakkar","el-Atiqa Akkar Aakkar","Akroum Aakkar","Issa Rajm w Aamair Al Aakkar",
        "Aboudiyeh Al Aakkar","Awainat Al Aakkar","Bireh Al Aakkar","Burj Al Aakkar",
        "Farid Al Aakkar","Hakour Al Aakkar","Hishah Al Aakkar","Hissa Al Aakkar","Hmayra Al Aakkar",
        "Kweikhat Al Aakkar","Majdal Al Aakkar","Maqybleh Al Aakkar","Qariyat Al Aakkar",
        "Qobeiyat Al Aakkar","Qurnah Al Aakkar","Talil Al Aakkar","Al-Ayoun Aakkar",
        "Al-Dabbabiya Aakkar","Al-Kwashra Aakkar","Al-Mahmara Aakkar","Al-Maqeeta Aakkar",
        "Al-Mounasseh Aakkar","Al-Qantara Aakkar","Al-Qarqaf Aakkar","Al-Rihaneya Aakkar",
        "Ayyash Al-Sheikh Aakkar","Al-Beykat Ammar Aakkar","Nafiseh An Aakkar",
        "Harsh Al Bestan and Naheriyah An Aakkar","Andqet Aakkar","Arqa Aakkar","Sulah As Aakkar",
        "Shuqduf Ash Aakkar","al-Ghazlan Ayun Aakkar","Ayyat Aakkar","Sakhr Bani Aakkar",
        "Barbarah Aakkar","Barkaayl Aakkar","Qaboula - Bayno Aakkar","Ayyub Bayt Aakkar",
        "Mlat Bayt Aakkar","Bazal Aakkar","Bazbina Aakkar","Abdeh Al - Bebnine Aakkar",
        "Hajj El Beit Aakkar","Younes Beit Aakkar","Biqrazla Aakkar","Arab Al Burj Aakkar",
        "Qanbar al Dahr Aakkar","Laysina Dahr Aakkar","al-Maqasarin Zouk and Dalloum Deir Aakkar",
        "Janine Deir Aakkar","Dura Aakkar","Baghdad and Dusa Aakkar","Adwiya Dweir Aakkar",
        "Eilat Aakkar","Tenta Ain and Ashma Ain Fassikin, Aakkar","Fnaideq Aakkar","Ghazilah Aakkar",
        "Halba Aakkar","Harrar Aakkar","Haytla Aakkar","Hayzouq Aakkar","Rama Ar and Jarmnaya Aakkar",
        "Juma Al Jdeideh Aakkar","Qaytaa Al Jdeideh Aakkar","Jebrayel Aakkar",
        "Naheriyeh Al Mazraat Ghattas, Beit Aassfour, Karm Aakkar","Kfarton Aakkar",
        "Shar Kharba Aakkar","Dawud Kharbit Aakkar","Petrol al Khat Aakkar","Khuraibeh Aakkar",
        "Kousha Aakkar","Arab Kroom Aakkar","Majdala Aakkar","Mamna Aakkar","Touma Mar Aakkar",
        "Mashha Aakkar","Bleda Mazraat Aakkar","Minyara Aakkar","Mishmish Aakkar","Munjaz Aakkar",
        "Hamoud Mushta Aakkar","Al-Tahata and Al-Fawqa Nurah Aakkar","Qaliyat Aakkar",
        "Semqley - Chamra Qoubbet Aakkar","Qubayyat Aakkar","Quneya Aakkar","Rahba Aakkar",
        "Rimah Aakkar","Al-Qetaa Safinat Aakkar","al-Dreib Safinet Aakkar","Raydan Sandiyaneh Aakkar",
        "Shan Aakkar","Sharbila Aakkar","Aadbal - Mohammad Sheikh Aakkar","Taba Sheikh Aakkar",
        "Shiddreh Aakkar","Sissouk Aakkar","Swayseh Aakkar","Takrit Aakkar","Gharbi Al Abbas Tal Aakkar",
        "Washataha Talla Aakkar","Talmaayan Aakkar","Tasha Aakkar","Al-Hawr Wadi Aakkar",
        "al-Jamus Wadi Aakkar","Khalid Wadi Aakkar","Zawarib Aakkar","al-Hssayne Zouk Aakkar",
        "Hadara Zouk Aakkar","حوبش", "Others"],
    "Baalbek-Hermel": [
        "Ahmar Al Deir",
        "Ainata",
        "Al-Ain",
        "Al-Fawqa Sareen",
        "Al-Laboue",
        "Alaa Hurit",
        "Alaqa Al and Boudai",
        "Ansar",
        "Baalbek",
        "Baalbek - West - Shamstaar",
        "Barqa",
        "Bdenayel",
        "Berda Houch",
        "Bishwat",
        "Brital",
        "Btedai",
        "Douris",
        "Dumdum Al Nabha",
        "Fa'rah Wadi",
        "Fissan",
        "Flawi",
        "Foqa Al Tannin",
        "Halabat",
        "Harbata",
        "Harfoush and Qaleela",
        "Hashish Al Jawar",
        "Hazin",
        "Iaat",
        "Jaba'a",
        "Jabule",
        "Jubayniyah Al and Ram",
        "Jinta",
        "Kawakh",
        "Kfardan",
        "Ma'arabun",
        "Mahfara Al Nabha",
        "Majdaloun",
        "Mqneh",
        "Naba Qasr",
        "Nahle",
        "Nabi Al Hawsh",
        "Othman Al-Nabi",
        "Qadam Al Nabha",
        "Qarah",
        "Qasr",
        "Rafiqah Al Hawsh",
        "Safiye Tel Houch",
        "Saneed Hawsh",
        "Shaath",
        "Sheet Al-Nabi",
        "Tahta Al Serain",
        "Tahta Al Tannin",
        "Talya",
        "Tariya",
        "Thta Al wa Fawqa Al Shawagir",
        "Tawfiqiyah",
        "Yunin",
        "Zabud",
        "Zarazir", "Others"],
    "Bekaa": [
        "Aana Bekaa Western","Abilh Zahle","Arab Ain Rachaiya","Ata Ain Rachaiya","Tinah El Ain Bekaa Western",
        "Harsha Ain Rachaiya","Kafarzabad Ain Zahle","Zabda Ain Bekaa Western","Manara Al Bekaa Western",
        "Mansoura Al Bekaa Western","Rawda Al Bekaa Western","Al-Aqaba Rachaiya","Al-Bireh Rachaiya",
        "Al-Khiyara Bekaa Western","Al-Muheithrah Rachaiya","Al-Muruj Bekaa Western","Al-Rafid Rachaiya",
        "Al-Sawiri Bekaa Western","Al-Nahri Ali Zahle","Ameq Bekaa Western","Aytanit Bekaa Western",
        "Ba'loul Bekaa Western","Mare' Bab Bekaa Western","Elias Bar Zahle","Bawarj Zahle",
        "Lahia Beit Rachaiya","Bkaa Rachaiya","Bkifa Rachaiya","Chatura Zahle","Al-Ashayer Deir Rachaiya",
        "Al-Ghazal Deir Zahle","Al-Fakhar Eita Rachaiya","Eyha Rachaiya","Ferzol Zahle","Gaza Bekaa Western",
        "Halawa Rachaiya","Al-Fikani Hay Zahle","Hazerta Zahle","Al-Harimeh Hosh Bekaa Western",
        "Al-Qanaba Hosh Rachaiya","Moussa Hosh Zahle","Jenin Jaba Bekaa Western","Danis Kafr Rachaiya",
        "Salsata Mazraat - Mashki Kafr Rachaiya","Qouq Kafr Rachaiya","Kafraya Bekaa Western",
        "Al-Lawz Kamid Bekaa Western","Kawkaba Rachaiya","Kfarzabad Zahle","Qanafar Khirbet Bekaa Western",
        "Rouha Khirbet Rachaiya","Lala Bekaa Western","Lubya Bekaa Western",
        "Taanayel and Maaloula Zahle","Anjar Majdal Zahle","Fadel Bani Majdal Rachaiya",
        "Makse Zahle","Mashgharah Bekaa Western","Massa Zahle","Lussia and Midoun Bekaa Western",
        "Mrayjet Zahle","Mudawwara Rachaiya","Nasiriya Zahle","Niha Zahle","Qilya Bekaa Western",
        "El-Dleim Wadi - Elias Qob Zahle","Qousaya Zahle","Rashaya Rachaiya","Hala Housh - Riak Zahle",
        "Riyat Zahle","Saadnayel Zahle","Saghbin Bekaa Western","Sahmara Bekaa Western",
        "almuahada Ya'qub Sultan Bekaa Western","Talabayya Zahle","Dzanoub Tall Bekaa Western",
        "Tannourine Rachaiya","Trebil Zahle","Yahmar Bekaa Western","Yanta Rachaiya","Zahl", "Others"],
    "Beirut": ["Beirut", "Others"],
    "Mount Lebanon": [
        "Aaaroun Matn",
        "Aaqbiyeh Kesrouane",
        "Achqout Bkaatouta Kesrouane",
        "Ad-Dahr Mazraat Chouf El",
        "Aeroun Matn",
        "Ahmouch Byblos",
        "Ajaltoun Kesrouane",
        "Ainab Aalay",
        "Ainab Chouf El",
        "Ainout Chouf El",
        "Aintoura Kesrouane",
        "Aitryoun Chouf El",
        "Al-Azra Kesrouane",
        "Al-Barajneh Burj Baabda",
        "Al-Barghoutiyya at Mzaira and Aalman Chouf El",
        "Al-Dafnah and Adma Kesrouane",
        "Al-Ghadeer-Al-Lailka Al-Muraijeh-Tahweta Baabda",
        "Al-Ghayneh Kesrouane",
        "Al-Kosiba Baabda",
        "Al-Urbaniyah-Al-Dalibah Baabda",
        "Al-Rehanah Ain Kesrouane",
        "Al-Kosiba Baabda",
        "Al-Ghadeer-Al-Lailka Al-Muraijeh-Tahweta Baabda",
        "Al-Kosiba Baabda",
        "Aqoura Al Byblos",
        "Aramoun Kesrouane",
        "Arsoun Jouret Baabda",
        "Arayya Baabda",
        "Ashqout Kesrouane",
        "Az-Zuweiriyah Chouf El",
        "Badran Jourat Kesrouane",
        "Baabdat Matn",
        "Baadaran Chouf El",
        "Baakline Chouf El",
        "Baassir Chouf El",
        "Ballout El Ruwayset Baabda",
        "Barja Chouf El",
        "Bassaba Chouf El",
        "Batater Aalay",
        "Bater Chouf El",
        "Batgrine Matn",
        "Batha Kesrouane",
        "Baysour Aalay",
        "Bdeghan Aalay",
        "Biknaya - Dib El Jal Matn",
        "Blat-Aoukar Khrab-Haret El Dbayeh-Zouk Matn",
        "Blouneh Kesrouane",
        "Bmariam Baabda",
        "Bneyeh Al Aalay",
        "Bqaatouta Kesrouane",
        "Broumana Matn",
        "Bware Al Kesrouane",
        "Byakout Matn",
        "Bzebdine Baabda",
        "Bzommar Kesrouane",
        "Chabab Beit Matn",
        "Chalhoub Zalka-Ammar Matn",
        "Chanehye Aalay",
        "Charoun Aalay",
        "Chehim Chouf El",
        "Chiyah Baabda",
        "Chouf El Jdeideh Chouf El",
        "Chouf El Maasser Chouf El",
        "Dalbatta Kesrouane",
        "Dalhoun Chouf El",
        "Daisheh Ad-Maklas Al-Mansouriyah Al Matn",
        "Daraya Chouf El",
        "Daroun Kesrouane",
        "Darya Kesrouane",
        "Dawwar Al-Musa Mar Matn",
        "Dawwar Matn",
        "Dfoun Aalay",
        "DoukMakayl Kesrouane",
        "El-Mghara Dahr Chouf El",
        "Faitroun Kesrouane",
        "Fanar Matn",
        "Faraya Kesrouane",
        "Fatqa Kesrouane",
        "Fatri Byblos",
        "Fil el Sin Matn",
        "Furn Baabda",
        "Ghabaleh Kesrouane",
        "Gharife Chouf El",
        "Ghazir Kesrouane",
        "Ghobeiry Baabda",
        "Ghodras Kesrouane",
        "Ghousta Kesrouane",
        "Ghabbah Al Matn",
        "Haouz Al Jewar Baabda",
        "Halat Byblos",
        "Hammana Baabda",
        "Hammoud Bourj Matn",
        "Harf Al Ras Baabda",
        "Harf El Deir Baabda",
        "Harajel Kesrouane",
        "Hasbaya Baabda",
        "Hasin Al Kesrouane",
        "Hasrout Chouf El",
        "Haytah Kesrouane",
        "Hazmieh Baabda",
        "Hreik Haret Baabda",
        "Hilalia Baabda",
        "Houdaira El Mazraat - Chaar El Beit Matn",
        "Ibrahim Nahr Byblos",
        "Jaj Byblos",
        "Jbaa Chouf El",
        "Jbeil Byblos",
        "Jdeideh Kesrouane",
        "Jedra Chouf El",
        "Jiyeh Chouf El",
        "Joueita Kesrouane",
        "Joun Chouf El",
        "Jounieh Kesrouane",
        "Jarif Kfar & Nemoura Kesrouane",
        "Kako El Aar-Beit Chehwan-Ain Qornet Matn",
        "Kaifun Aalay",
        "Karam Al Baabda",
        "Karya Al Baabda",
        "Kfardbian Kesrouane",
        "Kfarmatta Aalay",
        "Kfarselwan Baabda",
        "Kfertay Kesrouane",
        "Kfouar Kesrouane",
        "Khuraibeh Baabda",
        "Kholouniyeh Al Chouf El",
        "Khreibeh Al Chouf El",
        "Lassa Byblos",
        "Majdlaya Aalay",
        "Majdoub Al-Mazraa-Bsallim Matn",
        "Marj al Ain Mansouriya Al Aalay",
        "Matallah Al Chouf El",
        "Mazboud Chouf El",
        "Mazkah Al-Chaaya Mar Matn",
        "Merouba Kesrouane",
        "Meri Beit Matn",
        "Mghayriyeh Chouf El",
        "Mhaid El Jouret W Chehatoal Kesrouane",
        "Mosbeh Zouk Kesrouane",
        "Muhaidatha Al-Bikfaya Matn",
        "Mrayjet & Bourjein Chouf El",
        "Mristi Chouf El",
        "Mukhtara Al Chouf El",
        "Nahr El Tahwitet - Remmaneh El Ain - Chebbak El Furn",
        "Naqash Al-Antelias Matn",
        "Niha Chouf El",
        "Nabiheet Matn",
        "Oyoun Al Matn",
        "Qabi` Baabda",
        "Qartaba Byblos",
        "Qattara Al Mifouk Byblos",
        "Qulayat Al Kesrouane",
        "Rabieh Matn",
        "Rachin Kesrouane",
        "Reefoun Kesrouane",
        "Remhala Aalay",
        "Rmeileh Chouf El",
        "Roumiyeh Matn",
        "Rmeileh Chouf El",
        "Safa Al-Misk-Bahr Saqiyat Matn",
        "Safra Kesrouane",
        "Sahylih Al Kesrouane",
        "salima Baabda",
        "Shabaniya Baabda",
        "Shennaya Kesrouane",
        "Shuwit Baabda",
        "Sibline Chouf El",
        "Smakiah Chouf El",
        "Sofar Aalay",
        "Tabarja Kesrouane",
        "Tarshish Baabda",
        "Tartij Byblos",
        "Wardanieh Chouf El",
        "Yashouh Mazraat Matn",
        "Yahchouch Kesrouane",
        "Zaaitra Kesrouane",
        "Zaytoun Kesrouane", "Others"],
    "North Lebanon": [
        "Aabrin",
        "Aakrine",
        "Aal Mina",
        "Aimar",
        "Ajdabra",
        "Ajdabrin",
        "Al-Badawi",
        "Al-Hazmiyeh",
        "Al-Majdal",
        "Al-Mina",
        "Al-Qalamoun",
        "Al-Safira",
        "Amyoun",
        "Anfeh",
        "Asia",
        "Asoun",
        "Ayal",
        "Baan",
        "Bakhoun",
        "Banshie",
        "Basliqit",
        "Bassirma",
        "Batarmaz",
        "Batram",
        "Batroumine",
        "Bcoza and Namreen",
        "Bazoun",
        "Bchamzin",
        "Bdebba",
        "Bdenaile",
        "Bechtar Dar",
        "Bela Deir",
        "Bkoza and Namreen",
        "Bkrkasha",
        "Bqarsouna",
        "Bqosta",
        "Bshaleh",
        "Bsharri",
        "Btaaboura",
        "Btouratije",
        "Bursa",
        "Bziza",
        "Chatine",
        "Chlala",
        "Chmizzine",
        "Darya-Bishnin",
        "Dede",
        "Douma",
        "Ezaki",
        "Fiyeh",
        "Fawar Al Harat",
        "Hamat",
        "Heri",
        "Hassroun",
        "Izal",
        "Jebbeh El Hadath",
        "Jran",
        "Kaftoun",
        "Kassab Bayt - Hardine",
        "Kfaraarabi",
        "Kfarabida",
        "Kfarahezir",
        "Kfaraka",
        "Kfarbanin",
        "Kfarchi",
        "Kfardfou",
        "Kfardlakos",
        "Kfarhabu",
        "Kfarhata",
        "Kfarhatta",
        "Kfarhelda",
        "Kfarsaroun",
        "Kfaryachit-Bassbaal",
        "Kfraya",
        "Koubba",
        "Kour",
        "Kousba",
        "Majdalia",
        "Markabta",
        "Metrith",
        "Nahash Ras",
        "Qannat",
        "Qolehate",
        "Qorsayta",
        "Rachadbin",
        "Rachiine",
        "Salata",
        "Saraal",
        "Seer",
        "Shaayt Hdad",
        "Shbatin",
        "Tannourine",
        "Taran",
        "Tehoum",
        "Tuffah Al Mazraat",
        "Tourine",
        "Tourza",
        "Tripoli",
        "Zan",
        "Zgharta-Ehden", "Others"],
    "South Lebanon": [
        "Aabra Saida","Aarai Jezzine","Adloun Saida","Adousiyeh Saida","Baal Ain Sour","Eddelb Ain Saida",
        "Abbasiyah Al Sour","Bayyad Al Sour","Bazuriyah Al Sour","Bisariyah Al Saida","Burghliye Al Sour",
        "Bustan Al Sour","Hamiri Al Sour","Hilaliyah Al Saida","Hlousiyeh Al Sour","Jibbin Al Sour",
        "Lubiyah Al Saida","Maknouneh Al Jezzine","Mansouri Al Sour","Marwaniyah Al Saida",
        "Mayy Wal Mayy Al Saida","Midan Al Jezzine","Qulaylah Al Sour","Quryah Al Saida",
        "Sahel Al Malikiyat and Shaatiye Al Sour","Al-Eishiyeh Jezzine","Al-Hamssiyeh Jezzine",
        "Al-Louwayzeh Jezzine","Al-Rayhan Jezzine","Alhinya Sour","Alkanisa Sour","Shaaab Ash Alma Sour",
        "Alzahira Sour","Najariyah An Saida","Naqoura An Sour","Anqoun Saida","Ansariyah Saida",
        "Aramta Jezzine","Arzoun Sour","Aytit Sour","Azour Jezzine","Babliyeh Saida","Baksata Saida",
        "Baramiyeh Saida","Batoulieh Sour","Bedeas Sour","dependencies its and Bkassine Jezzine",
        "Bnouhate Jezzine","Shamali Al Bourj Sour","Abdallah Abou Ain and Rahhal Bourj Sour",
        "Al-Laqch Bteddine Jezzine","Amess Deir Sour","Keifa Deir Sour","Nahr En Qanoun Deir Sour",
        "Ain Al Ras Qanoun Deir Sour","Essim Derb Saida","Dirdghayya Sour","Ghassaniyeh Saida",
        "Ghazieh Saida","Saida Haret Saida","Haytoura Jezzine","Hinawiye Sour","Albutm Jabal Sour",
        "Jannata Sour","Majdeline Ain - Jezzine Jezzine","Jrania Jezzine","Karkha Jezzine",
        "al-Siyad Kawthariyat Saida","Jirra Kfar Jezzine","Kfarfalous Jezzine","Khartoum Saida",
        "Labaa Jezzine","Maaroub Sour","Majadel Sour","Majdal Jezzine","Majdalyoun Saida",
        "Majdalzoun Sour","Marwahine Sour","Moshref Mazraat Sour","Mchmoush", "Others"],
    "Nabatieh": [
        "Aaba", "Adchit", "Al-Fardis", "Al-Fawqa", "Al-Gharbiya Sair",
        "Al-Gharbiya Zawtar",
        "Al-Habariyah",
        "Al-Kafr",
        "Al-Khalwat",
        "Al-Sharkiya",
        "Al-Tahta Houmine",
        "Ansar",
        "Arabsalim",
        "Arnoun",
        "Bariqaa",
        "Bridge Kaakaiye",
        "Choukeen",
        "Doueir",
        "Ezza",
        "Fila Kafr",
        "Habbouch",
        "Harouf",
        "Jargea",
        "Jbaa",
        "Jibchit",
        "Kfour",
        "Mayfadoun",
        "Mimas",
        "Nabatieh",
        "Nemriye",
        "Rumine",
        "Ruman Kafr",
        "Sarbah",
        "Seen",
        "Shuba Kafr",
        "Yohmor",
        "Zefta",
        "Zibdeen", "Others"]
};


const governorateSelect = document.getElementById('governorate');
const citySelect = document.getElementById('city');
const otherCityInput = document.getElementById('other_city');

// Populate city dropdown on governorate change
governorateSelect.addEventListener('change', () => {
    const gov = governorateSelect.value;
    citySelect.innerHTML = '<option value="">Select City</option>'; // reset

    if (municipalities[gov]) {
        municipalities[gov].forEach(city => {
            const opt = document.createElement('option');
            opt.value = city;
            opt.textContent = city;
            citySelect.appendChild(opt);
        });
    }

    otherCityInput.style.display = 'none';
    otherCityInput.value = '';
});

// Show free text field if "Others" is selected
citySelect.addEventListener('change', () => {
    if (citySelect.value === 'Others') {
        otherCityInput.style.display = 'block';
    } else {
        otherCityInput.style.display = 'none';
        otherCityInput.value = '';
    }
});
</script>
<!-- =================== Position & Requirements Box =================== -->
<div class="box">
 <h3>Position & Requirements</h3>
    <label>10. Advertised Job Title</label>
    <input type="text" name="Job_Title" id="job_title" placeholder="Software Engineer" autocomplete="off">
    <div id="suggestions" class="autocomplete-suggestions" style="border:1px solid #ccc; max-height:150px; overflow-y:auto;"></div>

    <script>
    const input = document.getElementById('job_title');
    const suggestionsBox = document.getElementById('suggestions');

    input.addEventListener('input', function() {
        const query = this.value.trim().toLowerCase();
        if(query.length < 1) {
            suggestionsBox.innerHTML = '';
            return;
        }

        fetch(`/search_title?q=${query}`)
            .then(response => response.json())
            .then(data => {
                suggestionsBox.innerHTML = '';
                data.forEach(item => {
                    const div = document.createElement('div');
                    div.classList.add('autocomplete-suggestion');

                    // Highlight matched text
                    const regex = new RegExp(`(${query})`, 'gi');
                    div.innerHTML = item.replace(regex, '<strong>$1</strong>');

                    // Click to select
                    div.addEventListener('click', function() {
                        input.value = item;
                        suggestionsBox.innerHTML = '';
                    });

                    suggestionsBox.appendChild(div);
                });
            });
    });

    // Optional: close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if(!suggestionsBox.contains(e.target) && e.target !== input) {
            suggestionsBox.innerHTML = '';
        }
    });
    </script>

    <style>
    .autocomplete-suggestions div {
        padding: 5px 10px;
        cursor: pointer;
    }
    .autocomplete-suggestions div:hover {
        background-color: #e0e0e0;
    }
    </style>

    <label>11. Work Modality:</label>
    <div class="radio-group" style="display:flex; justify-content:center; gap:100px; margin-top:10px;">
        <!-- Employment Type -->
        <div style="text-align:center;">
            <strong>Employment Type:</strong><br>
            <div style="display:flex; gap:20px; justify-content:center; margin-top:5px;">
                <label><input type="radio" name="Employment_Type" value="Part-time"> Part-time</label>
                <label><input type="radio" name="Employment_Type" value="Full-time"> Full-time</label>
            </div>
        </div>

        <!-- Location -->
        <div style="text-align:center;">
            <strong>Location:</strong><br>
            <div style="display:flex; gap:20px; justify-content:center; margin-top:5px;">
                <label><input type="radio" name="Location" value="Office"> Office</label>
                <label><input type="radio" name="Location" value="Remote"> Remote</label>
                <label><input type="radio" name="Location" value="Hybrid"> Hybrid</label>
            </div>
        </div>
    </div>

    <label>12. Work Schedule:</label>
    <input type="text" name="Work_Schedule" placeholder="e.g., 9 AM – 5 PM, shifts">

    <div style="display: flex; gap: 20px; align-items: center;">
        <div style="flex: 1;">
            <label for="posting_date">13. Posting Date</label>
            <input type="date" id="posting_date" name="Posting_Date" style="width: 100%;">
        </div>
        <div style="flex: 1;">
            <label for="closing_date">Closing Date</label>
            <input type="date" id="closing_date" name="Closing_Date" style="width: 100%;">
        </div>
    </div>

    <label>14. Duration of initial contract</label>
    <div style="display: flex; gap: 10px; align-items: center;">
        <input type="text" name="Contract_Duration" placeholder="6" style="width:60px;">
        <select name="Contract_Unit" style="width:100px;">
            <option value="days">Days</option>
            <option value="weeks">Weeks</option>
            <option value="months" selected>Months</option>
            <option value="years">Years</option>
        </select>
    </div>

    <label>15. Probation period?</label>
    <div style="display: flex; gap: 20px; align-items: center; margin-top: 5px;">
        <label style="text-align: center; display: flex; flex-direction: column; align-items: center;">
            <input type="radio" name="Probation" value="Yes"> Yes
        </label>
        <label style="text-align: center; display: flex; flex-direction: column; align-items: center;">
            <input type="radio" name="Probation" value="No"> No
        </label>
    </div>

    <!-- Hidden input for probation duration -->
    <input type="text" id="probation_duration" name="Probation_Duration" placeholder="Specify duration" style="display:none; margin-top:5px; width:150px;">

    <script>
    const probationRadios = document.getElementsByName('Probation');
    const probationInput = document.getElementById('probation_duration');

    probationRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'Yes' && radio.checked) {
                probationInput.style.display = 'block';
            } else if (radio.value === 'No' && radio.checked) {
                probationInput.style.display = 'none';
                probationInput.value = '';
            }
        });
    });
    </script>
    
    <label>16. Nationality Requirement?</label>
    <div style="display: flex; gap: 20px; align-items: center; margin-top: 5px;">
        <label style="text-align: center; display: flex; flex-direction: column; align-items: center;">
            <input type="radio" name="Nationality_Req" value="Yes"> Yes
        </label>
        <label style="text-align: center; display: flex; flex-direction: column; align-items: center;">
            <input type="radio" name="Nationality_Req" value="No"> No
        </label>
    </div>

    <!-- Hidden input for specifying nationality -->
    <input type="text" id="nationality_specify" name="Nationality_Specify" placeholder="Specify nationality" style="display:none; margin-top:5px; width:200px;">

    <script>
    const nationalityRadios = document.getElementsByName('Nationality_Req');
    const nationalityInput = document.getElementById('nationality_specify');

    nationalityRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'Yes' && radio.checked) {
                nationalityInput.style.display = 'block';
            } else if (radio.value === 'No' && radio.checked) {
                nationalityInput.style.display = 'none';
                nationalityInput.value = '';
            }
        });
    });
    </script>

    <label>17. Degree</label>
    <select name="Degree_Details">
        <option value="" disabled selected>Select degree</option>
        <option value="High School Diploma">High School Diploma</option>
        <option value="Technical Diploma">Technical Diploma</option>
        <option value="Bachelor degree">Bachelor degree</option>
        <option value="Master degree">Master degree</option>
        <option value="PhD">PhD</option>
        <option value="Not specified">Not specified</option>
    </select>

<label>18. Specialization</label>
<div class="specialization-container">
    <div class="input-wrapper">
        <input type="text" class="specialization-input" placeholder="Select or type a specialization..." oninput="filterOptions(this)" onclick="showOptions(this)">
        <div class="options-list"></div>
    </div>
    <div class="input-wrapper">
        <input type="text" class="specialization-input" placeholder="Select or type a specialization..." oninput="filterOptions(this)" onclick="showOptions(this)">
        <div class="options-list"></div>
    </div>
    <div class="input-wrapper">
        <input type="text" class="specialization-input" placeholder="Select or type a specialization..." oninput="filterOptions(this)" onclick="showOptions(this)">
        <div class="options-list"></div>
    </div>
</div>

<style>
.specialization-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 500px;
}

.input-wrapper {
    position: relative; /* anchor for absolute dropdown */
    width: 100%;
}

.specialization-input {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    width: 100%;
    box-sizing: border-box;
}

.options-list {
    position: absolute;
    top: 100%;
    left: 0;
    background: white;
    border: 1px solid #ccc;
    max-height: 150px;
    overflow-y: auto;
    width: 100%;
    z-index: 1000;
    display: none;
}

.options-list div {
    padding: 5px 10px;
    cursor: pointer;
}

.options-list div:hover {
    background-color: #f0f0f0;
}
</style>

<script>
const iscedOptions = [ "None", "Generic programmes and qualifications not further defined", "Basic programmes and qualifications", "Literacy and numeracy", "Personal skills and development", "Generic programmes and qualifications not elsewhere classified", "Education not further defined", "Education science", "Training for pre-school teachers", "Teacher training without subject specialization", "Teacher training with subject specialization", "Education not elsewhere classified", "Inter-disciplinary programmes and qualifications involving education", "Arts and humanities not further defined", "Arts not further defined", "Audio-visual techniques and media production", "Fashion, interior and industrial design", "Fine arts", "Handicrafts", "Music and performing arts", "Arts not elsewhere classified", "Humanities (except languages) not further defined", "Religion and theology", "History and archaeology", "Philosophy and ethics", "Humanities (except languages) not elsewhere classified", "Languages not further defined", "Language acquisition", "Literature and linguistics", "Languages not elsewhere classified", "Inter-disciplinary programmes and qualifications involving arts and humanities", "Arts and humanities not elsewhere classified", "Social sciences, journalism and information not further defined", "Social and behavioural sciences not further defined", "Economics", "Political sciences and civics", "Psychology", "Sociology and cultural studies", "Social and behavioural sciences not elsewhere classified", "Journalism and information not further defined", "Journalism and reporting", "Library, information and archival studies", "Journalism and information not elsewhere classified", "Inter-disciplinary programmes and qualifications involving social sciences, journalism and information", "Social sciences, journalism and information not elsewhere classified", "Business, administration and law not further defined", "Business and administration not further defined", "Accounting and taxation", "Finance, banking and insurance", "Management and administration", "Marketing and advertising", "Secretarial and office work", "Wholesale and retail sales", "Work skills", "Business and administration not elsewhere classified", "Law", "Inter-disciplinary programmes and qualifications involving business, administration and law", "Business, administration and law not elsewhere classified", "Natural sciences, mathematics and statistics not further defined", "Biological and related sciences not further defined", "Biology", "Biochemistry", "Biological and related sciences not elsewhere classified", "Environment not further defined", "Environmental Sciences", "Natural Environments and wildlife", "Environment not elsewhere classified", "Physical sciences not further defined", "Chemistry", "Earth sciences", "Physics", "Physical sciences not elsewhere classified", "Mathematics and statistics not further defined", "Mathematics", "Statistics", "Inter-disciplinary programmes and qualifications involving Natural sciences, mathematics and statistics", "Natural sciences, mathematics and statistics not elsewhere classified", "Information and Communication Technologies (ICTs) not further defined", "Computer Use", "Database and network design and Administration", "Software and applications development and analysis", "Information Communication Technologies (ICTs) not elsewhere classified", "Inter-disciplinary programmes and qualifications involving Information and Communication Technologies (ICTs)", "Engineering, manufacturing and construction not further defined", "Engineering and engineering trades not further defined", "Chemical engineering and processes", "Environmental protection technology", "Electricity and energy", "Electronics and automation", "Mechanics and metal trades", "Motor vehicles, ships and aircraft", "Engineering and engineering trades not elsewhere classified", "Manufacturing and processing not further defined", "Food processing", "Materials (glass, paper, plastic and wood)", "Textiles (clothes, footwear and leather)", "Mining and extraction", "Manufacturing and processing not elsewhere classified", "Architecture and construction not further defined", "Architecture and town planning", "Building and civil engineering", "Inter-disciplinary programmes and qualifications involving engineering, manufacturing and construction", "Engineering, manufacturing and construction not elsewhere classified", "Agriculture, forestry, fisheries and veterinary not further defined", "Agriculture not further defined", "Crop and livestock production", "Horticulture", "Agriculture not elsewhere classified", "Forestry", "Fisheries", "Veterinary Services", "Inter-disciplinary programmes and qualifications involving agriculture, forestry, fisheries and veterinary services", "Agriculture, forestry, fisheries and veterinary not elsewhere classified", "Health and welfare not further defined", "Health not further defined", "Dental studies", "Medicine", "Nursing and midwifery", "Medical diagnostic and treatment technology", "Therapy and rehabilitation", "Pharmacy", "Traditional and complementary medicine and therapy", "Health not elsewhere classified", "Welfare not further defined", "Care of the elderly and of disabled adults", "Child care and youth services", "Social work and counselling", "Welfare not elsewhere classified", "Inter-disciplinary programmes and qualifications involving health and welfare", "Health and welfare not elsewhere classified", "Services not further defined", "Personal services not further defined", "Domestic services", "Hair and beauty services", "Hotel, restaurants and catering", "Sports", "Travel, tourism and leisure", "Personal services not elsewhere classified", "Hygiene and occupational health services not further defined", "Community sanitation", "Occupational health and safety", "Hygiene and occupational Health Services not elsewhere classified", "Security services not further defined", "Military and defence", "Protection of persons and property", "Security services not elsewhere classified", "Transport services", "Inter-disciplinary programmes and qualifications involving services", "Services not elsewhere classified", "Field unknown" ];

function showOptions(input) {
    const list = input.nextElementSibling;
    list.style.display = 'block';
    renderOptions(list, input.value);
}

function filterOptions(input) {
    const list = input.nextElementSibling;
    renderOptions(list, input.value);
}

function renderOptions(list, filter) {
    list.innerHTML = '';
    const filtered = iscedOptions.filter(opt => opt.toLowerCase().includes(filter.toLowerCase()));
    filtered.forEach(option => {
        const div = document.createElement('div');
        div.textContent = option;
        div.onclick = (e) => {
            e.stopPropagation();
            list.previousElementSibling.value = option;
            list.style.display = 'none';
        };
        list.appendChild(div);
    });
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(e) {
    document.querySelectorAll('.options-list').forEach(list => {
        if(!list.previousElementSibling.contains(e.target) && !list.contains(e.target)) {
            list.style.display = 'none';
        }
    });
});
</script>

    <label>19. Languages</label>
    <table border="1" style="width: 60%; border-collapse: collapse; text-align: center;">
        <tr><th>Language</th><th>Reads</th><th>Writes</th><th>Speaks</th></tr>
        <tr>
            <td>Arabic</td>
            <td><input type="checkbox" name="Arabic_Read"></td>
            <td><input type="checkbox" name="Arabic_Write"></td>
            <td><input type="checkbox" name="Arabic_Speak"></td>
        </tr>
        <tr>
            <td>French</td>
            <td><input type="checkbox" name="French_Read"></td>
            <td><input type="checkbox" name="French_Write"></td>
            <td><input type="checkbox" name="French_Speak"></td>
        </tr>
        <tr>
            <td>English</td>
            <td><input type="checkbox" name="English_Read"></td>
            <td><input type="checkbox" name="English_Write"></td>
            <td><input type="checkbox" name="English_Speak"></td>
        </tr>
    </table>

    <button type="button" id="addLangBtn" style="margin-top:10px; padding: 5px 10px; font-size: 0.9em; width: 120px;">Add Language</button>

    <script>
    document.addEventListener("DOMContentLoaded", function(){
        const table = document.querySelector('table');
        document.getElementById('addLangBtn').addEventListener('click', function(){
            const newRow = table.insertRow(-1);
            newRow.innerHTML = `
                <td><input type="text" name="Other_Languages[]" placeholder="Language" style="width:120px;"></td>
                <td><input type="checkbox" name="Other_Read[]"></td>
                <td><input type="checkbox" name="Other_Write[]"></td>
                <td><input type="checkbox" name="Other_Speak[]"></td>
            `;
        });
    });
    </script>
   </br>
    <label>20. Years of Experience</label>
    <input type="text" name="Years_of_Experience_Required">
</div>

<!-- =================== Compensation & Benefits =================== -->
<div class="box">
    <h3>Compensation & Benefits</h3>
    <label>21. Salary Range</label>
    <div style="display:flex; gap:5px;">
        <input type="text" name="Salary_Range" placeholder="">
        <select name="Salary_Currency">
            <option value="LBP">LBP</option>
            <option value="USD">USD</option>
        </select>
    </div>

    <label>22. Other Allowances</label>
    <input type="text" name="Other_Allowances" placeholder="e.g., transportation, meals, phone">

    <label>23. Benefits</label>
    <table border="1" style="width: 60%; border-collapse: collapse; text-align: center;">
        <tr><th>Category</th><th>Benefit</th><th>Select</th></tr>
        <tr><td rowspan="4">Statutory & Core Benefits</td><td>NSSF (Social Security)</td><td><input type="checkbox" name="Benefits[]" value="NSSF (Social Security)"></td></tr>
        <tr><td>Annual Leave</td><td><input type="checkbox" name="Benefits[]" value="Annual Leave"></td></tr>
        <tr><td>Sick Leave</td><td><input type="checkbox" name="Benefits[]" value="Sick Leave"></td></tr>
        <tr><td>Parental Leave</td><td><input type="checkbox" name="Benefits[]" value="Parental Leave"></td></tr>
        <tr><td rowspan="2">Health & Protection</td><td>Health Insurance</td><td><input type="checkbox" name="Benefits[]" value="Health Insurance"></td></tr>
        <tr><td>Life Insurance / Disability Coverage</td><td><input type="checkbox" name="Benefits[]" value="Life Insurance / Disability Coverage"></td></tr>
        <tr><td rowspan="2">Family & Dependents</td><td>Dependents Compensation</td><td><input type="checkbox" name="Benefits[]" value="Dependents Compensation"></td></tr>
        <tr><td>Education Benefits</td><td><input type="checkbox" name="Benefits[]" value="Education Benefits"></td></tr>
        <tr><td>Housing & Allowances</td><td>Housing</td><td><input type="checkbox" name="Benefits[]" value="Housing"></td></tr>
    </table>
</div>

<!-- =================== Job Description & Skills =================== -->
<div class="box">
    <h3>Job Description</h3>

    <label>24. Background</label>
    <textarea name="Background" rows="3"></textarea>

    <label>25. Duties and Responsibilities</label>
    <textarea name="Duties_Responsibilities" rows="3"></textarea>

    <label>26. Tasks</label>
    <textarea name="Tasks" rows="3"></textarea>

    <!-- ======= Skills Section (26) ======= -->
<h3>27. Skills</h3>

<!-- Skill Input Method (Horizontal Radios) -->
<div style="margin-bottom:10px; display:flex; gap:20px; align-items:center;">
    <label><input type="radio" name="skill_method" value="option1" checked> Manual</label>
    <label><input type="radio" name="skill_method" value="option2"> From Job Title</label>
    <label><input type="radio" name="skill_method" value="option3"> Extract from Text</label>
</div>

<!-- Selected Skills Box -->
<div id="selected-skills" style="
    border:1px solid #ccc; padding:10px; min-height:40px;
    background:#fafafa; border-radius:5px; margin-bottom:10px;">
    <span style="color:#777;">No skills selected...</span>
</div>

<!-- ------------------- OPTION 1: Manual ------------------- -->
<div id="manual-box" style="display:block; margin-top:10px;">
    <label>Category</label>
    <select id="cat">
        <option value="">Loading...</option>
    </select>

    <label>Subcategory</label>
    <select id="subcat">
        <option value="">Select Subcategory</option>
    </select>

    <label>Skill</label>
    <select id="skill">
        <option value="">Select Skill</option>
    </select>

    <button type="button" onclick="addSelectedSkill()">Add</button>
</div>

<!-- ------------------- OPTION 2: From Job Title ------------------- -->
<div id="suggested-box" style="display:none; margin-top:10px;">
    <button type="button" onclick="getSuggestedSkills()">Load Skills</button>
    <div id="suggested-list" style="margin-top:10px;"></div>
</div>

<!-- ------------------- OPTION 3: Extract from Text ------------------- -->
<div id="extract-box" style="display:none; margin-top:10px;">
    <button type="button" onclick="extractSkills()">Extract Skills</button>
    <div id="extracted-list" style="margin-top:10px;"></div>
</div>

<script>
/* ===================== Data from Flask ===================== */
const allSkills = {{ skills_list|tojson }};
const categories = [...new Set(allSkills.map(s => s.category_name))].sort();

/* ===================== Elements ===================== */
const catSelect = document.getElementById("cat");
const subcatSelect = document.getElementById("subcat");
const skillSelect = document.getElementById("skill");
const selectedBox = document.getElementById("selected-skills");

let selectedSkills = [];

/* ===================== Render Selected Skills ===================== */
function renderSelected() {
    selectedBox.innerHTML = "";
    if (selectedSkills.length === 0) {
        selectedBox.innerHTML = "<span style='color:#777;'>No skills selected...</span>";
        return;
    }
    selectedSkills.forEach((skill, index) => {
        const tag = document.createElement("span");
        tag.style.cssText = `
            display:inline-block; background:#e3f2fd; color:#0277bd;
            padding:5px 10px; border-radius:20px; margin:5px;
        `;
        tag.innerHTML = `${skill} &nbsp; <b onclick="removeSkill(${index})" style="cursor:pointer; color:#c00;">✕</b>`;
        selectedBox.appendChild(tag);
    });
}

function removeSkill(i) { 
    selectedSkills.splice(i,1); 
    renderSelected(); 
}

/* ===================== Populate Categories ===================== */
function loadCategories() {
    catSelect.innerHTML = '<option value="">Select Category</option>';
    categories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c;
        opt.textContent = c;
        catSelect.appendChild(opt);
    });
}

/* ===================== Populate Subcategories for Category ===================== */
function loadSubcategories(cat) {
    const subs = [...new Set(allSkills
        .filter(s => s.category_name === cat)
        .map(s => s.subcategory_name))].sort();

    subcatSelect.innerHTML = '<option value="">Select Subcategory</option>';
    subs.forEach(sc => {
        const opt = document.createElement("option");
        opt.value = sc;
        opt.textContent = sc;
        subcatSelect.appendChild(opt);
    });
}

/* ===================== Populate Skills for Subcategory ===================== */
function loadSkills(cat, sub) {
    const skills = allSkills.filter(s =>
        s.category_name === cat && s.subcategory_name === sub
    );

    skillSelect.innerHTML = '<option value="">Select Skill</option>';
    skills.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.name;
        opt.textContent = s.name;
        skillSelect.appendChild(opt);
    });
}

/* ===================== Populate All Skills (for skill-first selection) ===================== */
function loadAllSkillsDropdown() {
    skillSelect.innerHTML = '<option value="">Select Skill</option>';
    allSkills.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.name;
        opt.textContent = s.name;
        skillSelect.appendChild(opt);
    });
}

/* ===================== Skill Selection (manual or pre-select) ===================== */
function selectOrAddSkill(skillName) {
    const skillObj = allSkills.find(s => s.name === skillName);
    if (!skillObj) return;

    // Fill category & subcategory
    catSelect.value = skillObj.category_name;
    loadSubcategories(skillObj.category_name);
    subcatSelect.value = skillObj.subcategory_name;
    loadSkills(skillObj.category_name, skillObj.subcategory_name);
    skillSelect.value = skillObj.name;

    // Add to selected skills
    if (!selectedSkills.includes(skillName)) selectedSkills.push(skillName);
    renderSelected();
}

/* ===================== Event Listeners ===================== */
catSelect.addEventListener("change", () => {
    const cat = catSelect.value;
    subcatSelect.innerHTML = '<option value="">Select Subcategory</option>';
    skillSelect.innerHTML = '<option value="">Select Skill</option>';
    if (!cat) return;
    loadSubcategories(cat);
});

subcatSelect.addEventListener("change", () => {
    const cat = catSelect.value;
    const sub = subcatSelect.value;
    skillSelect.innerHTML = '<option value="">Select Skill</option>';
    if (!cat || !sub) return;
    loadSkills(cat, sub);
});

skillSelect.addEventListener("change", () => {
    const skillName = skillSelect.value;
    if (!skillName) return;
    selectOrAddSkill(skillName);
});

/* ===================== Pre-select Skill Function ===================== */
function selectSkill(skillName) {
    selectOrAddSkill(skillName);
}

/* ===================== Option 2: From Job Title (EMSI API) ===================== */
function getSuggestedSkills() {
    const title = document.getElementById("job_title").value.trim();
    if (!title) { alert("Enter a Job Title first!"); return; }

    fetch("/get_api_skills", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ job_title: title })
    })
    .then(r => r.json())
    .then(data => {
        const list = document.getElementById("suggested-list");
        list.innerHTML = "";
        data.skills.forEach(s => {
            const div = document.createElement("div");
            div.style.cursor = "pointer";
            div.style.margin = "4px";
            div.textContent = s;
            div.onclick = () => selectOrAddSkill(s);
            list.appendChild(div);
        });
    })
    .catch(e => alert("Error fetching skills: " + e));
}

/* ===================== Option 3: Extract from Text (EMSI) ===================== */
function extractSkills() {
    const text = 
        (document.querySelector('textarea[name="Background"]').value || "") + " " +
        (document.querySelector('textarea[name="Duties_Responsibilities"]').value || "") + " " +
        (document.querySelector('textarea[name="Tasks"]').value || "");

    if (!text.trim()) { 
        alert("No job description text found!");
        return; 
    }

    fetch("/extract_from_text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
    })
    .then(r => r.json())
    .then(data => {
        const list = document.getElementById("extracted-list");
        list.innerHTML = "";

        data.skills.forEach(s => {
            const div = document.createElement("div");
            div.style.cursor = "pointer";
            div.style.margin = "4px";
            div.textContent = s;
            div.onclick = () => selectOrAddSkill(s);
            list.appendChild(div);
        });
    })
    .catch(err => {
        console.error(err);
        alert("Error extracting skills. See console.");
    });
}

/* ===================== Toggle Options (1–3) ===================== */
document.querySelectorAll("input[name='skill_method']").forEach(r => {
    r.addEventListener("change", function() {
        document.getElementById("manual-box").style.display = this.value === "option1" ? "block" : "none";
        document.getElementById("suggested-box").style.display = this.value === "option2" ? "block" : "none";
        document.getElementById("extract-box").style.display = this.value === "option3" ? "block" : "none";
    });
});

/* ===================== Initial Load ===================== */
loadCategories();
loadAllSkillsDropdown(); // populate all skills for skill-first selection
renderSelected();

/* ===================== Example: Pre-select skill ===================== */
// selectSkill("JavaScript"); // uncomment and replace with any skill
</script>
<div style="margin-top:15px; font-size:12px; line-height:1.4; font-style:italic;">
    <label style="cursor:pointer;"> 
        <input type="checkbox" 
               name="Equal_Opportunity" 
               value="Yes" 
               style="margin:0; padding:0; width:12px; height:12px; vertical-align:text-top;">
        We are an equal-opportunity employer and value diversity in all its forms. 
        All qualified individuals are encouraged to apply. Recruitment is conducted 
        anonymously and in line with Ministry of Labour standards to ensure 
        transparency, impartiality, and equal access for all candidates regardless 
        of gender, age, disability, religion, marital status, or any other characteristic.
    </label>
</div>

<input type="submit" value="Submit">
</body>
</html>
"""

# ==============================
# Municipalities data (Python dict) - same as اللي عطيتني
# ==============================

# ==============================
# Routes
# ==============================
municipalities =  {
    "Akkar": ["Daghlah Ad Aakkar","Aidmoon-Shekhlar Aakkar","al-Dhahab Ain Aakkar","al-Zayt Ain Aakkar",
        "Yaaqub Ain Aakkar","el-Atiqa Akkar Aakkar","Akroum Aakkar","Issa Rajm w Aamair Al Aakkar",
        "Aboudiyeh Al Aakkar","Awainat Al Aakkar","Bireh Al Aakkar","Burj Al Aakkar",
        "Farid Al Aakkar","Hakour Al Aakkar","Hishah Al Aakkar","Hissa Al Aakkar","Hmayra Al Aakkar",
        "Kweikhat Al Aakkar","Majdal Al Aakkar","Maqybleh Al Aakkar","Qariyat Al Aakkar",
        "Qobeiyat Al Aakkar","Qurnah Al Aakkar","Talil Al Aakkar","Al-Ayoun Aakkar",
        "Al-Dabbabiya Aakkar","Al-Kwashra Aakkar","Al-Mahmara Aakkar","Al-Maqeeta Aakkar",
        "Al-Mounasseh Aakkar","Al-Qantara Aakkar","Al-Qarqaf Aakkar","Al-Rihaneya Aakkar",
        "Ayyash Al-Sheikh Aakkar","Al-Beykat Ammar Aakkar","Nafiseh An Aakkar",
        "Harsh Al Bestan and Naheriyah An Aakkar","Andqet Aakkar","Arqa Aakkar","Sulah As Aakkar",
        "Shuqduf Ash Aakkar","al-Ghazlan Ayun Aakkar","Ayyat Aakkar","Sakhr Bani Aakkar",
        "Barbarah Aakkar","Barkaayl Aakkar","Qaboula - Bayno Aakkar","Ayyub Bayt Aakkar",
        "Mlat Bayt Aakkar","Bazal Aakkar","Bazbina Aakkar","Abdeh Al - Bebnine Aakkar",
        "Hajj El Beit Aakkar","Younes Beit Aakkar","Biqrazla Aakkar","Arab Al Burj Aakkar",
        "Qanbar al Dahr Aakkar","Laysina Dahr Aakkar","al-Maqasarin Zouk and Dalloum Deir Aakkar",
        "Janine Deir Aakkar","Dura Aakkar","Baghdad and Dusa Aakkar","Adwiya Dweir Aakkar",
        "Eilat Aakkar","Tenta Ain and Ashma Ain Fassikin, Aakkar","Fnaideq Aakkar","Ghazilah Aakkar",
        "Halba Aakkar","Harrar Aakkar","Haytla Aakkar","Hayzouq Aakkar","Rama Ar and Jarmnaya Aakkar",
        "Juma Al Jdeideh Aakkar","Qaytaa Al Jdeideh Aakkar","Jebrayel Aakkar",
        "Naheriyeh Al Mazraat Ghattas, Beit Aassfour, Karm Aakkar","Kfarton Aakkar",
        "Shar Kharba Aakkar","Dawud Kharbit Aakkar","Petrol al Khat Aakkar","Khuraibeh Aakkar",
        "Kousha Aakkar","Arab Kroom Aakkar","Majdala Aakkar","Mamna Aakkar","Touma Mar Aakkar",
        "Mashha Aakkar","Bleda Mazraat Aakkar","Minyara Aakkar","Mishmish Aakkar","Munjaz Aakkar",
        "Hamoud Mushta Aakkar","Al-Tahata and Al-Fawqa Nurah Aakkar","Qaliyat Aakkar",
        "Semqley - Chamra Qoubbet Aakkar","Qubayyat Aakkar","Quneya Aakkar","Rahba Aakkar",
        "Rimah Aakkar","Al-Qetaa Safinat Aakkar","al-Dreib Safinet Aakkar","Raydan Sandiyaneh Aakkar",
        "Shan Aakkar","Sharbila Aakkar","Aadbal - Mohammad Sheikh Aakkar","Taba Sheikh Aakkar",
        "Shiddreh Aakkar","Sissouk Aakkar","Swayseh Aakkar","Takrit Aakkar","Gharbi Al Abbas Tal Aakkar",
        "Washataha Talla Aakkar","Talmaayan Aakkar","Tasha Aakkar","Al-Hawr Wadi Aakkar",
        "al-Jamus Wadi Aakkar","Khalid Wadi Aakkar","Zawarib Aakkar","al-Hssayne Zouk Aakkar",
        "Hadara Zouk Aakkar","حوبش", "Others"],
    "Baalbek-Hermel": [
        "Ahmar Al Deir",
        "Ainata",
        "Al-Ain",
        "Al-Fawqa Sareen",
        "Al-Laboue",
        "Alaa Hurit",
        "Alaqa Al and Boudai",
        "Ansar",
        "Baalbek",
        "Baalbek - West - Shamstaar",
        "Barqa",
        "Bdenayel",
        "Berda Houch",
        "Bishwat",
        "Brital",
        "Btedai",
        "Douris",
        "Dumdum Al Nabha",
        "Fa'rah Wadi",
        "Fissan",
        "Flawi",
        "Foqa Al Tannin",
        "Halabat",
        "Harbata",
        "Harfoush and Qaleela",
        "Hashish Al Jawar",
        "Hazin",
        "Iaat",
        "Jaba'a",
        "Jabule",
        "Jubayniyah Al and Ram",
        "Jinta",
        "Kawakh",
        "Kfardan",
        "Ma'arabun",
        "Mahfara Al Nabha",
        "Majdaloun",
        "Mqneh",
        "Naba Qasr",
        "Nahle",
        "Nabi Al Hawsh",
        "Othman Al-Nabi",
        "Qadam Al Nabha",
        "Qarah",
        "Qasr",
        "Rafiqah Al Hawsh",
        "Safiye Tel Houch",
        "Saneed Hawsh",
        "Shaath",
        "Sheet Al-Nabi",
        "Tahta Al Serain",
        "Tahta Al Tannin",
        "Talya",
        "Tariya",
        "Thta Al wa Fawqa Al Shawagir",
        "Tawfiqiyah",
        "Yunin",
        "Zabud",
        "Zarazir", "Others"],
    "Bekaa": [
        "Aana Bekaa Western","Abilh Zahle","Arab Ain Rachaiya","Ata Ain Rachaiya","Tinah El Ain Bekaa Western",
        "Harsha Ain Rachaiya","Kafarzabad Ain Zahle","Zabda Ain Bekaa Western","Manara Al Bekaa Western",
        "Mansoura Al Bekaa Western","Rawda Al Bekaa Western","Al-Aqaba Rachaiya","Al-Bireh Rachaiya",
        "Al-Khiyara Bekaa Western","Al-Muheithrah Rachaiya","Al-Muruj Bekaa Western","Al-Rafid Rachaiya",
        "Al-Sawiri Bekaa Western","Al-Nahri Ali Zahle","Ameq Bekaa Western","Aytanit Bekaa Western",
        "Ba'loul Bekaa Western","Mare' Bab Bekaa Western","Elias Bar Zahle","Bawarj Zahle",
        "Lahia Beit Rachaiya","Bkaa Rachaiya","Bkifa Rachaiya","Chatura Zahle","Al-Ashayer Deir Rachaiya",
        "Al-Ghazal Deir Zahle","Al-Fakhar Eita Rachaiya","Eyha Rachaiya","Ferzol Zahle","Gaza Bekaa Western",
        "Halawa Rachaiya","Al-Fikani Hay Zahle","Hazerta Zahle","Al-Harimeh Hosh Bekaa Western",
        "Al-Qanaba Hosh Rachaiya","Moussa Hosh Zahle","Jenin Jaba Bekaa Western","Danis Kafr Rachaiya",
        "Salsata Mazraat - Mashki Kafr Rachaiya","Qouq Kafr Rachaiya","Kafraya Bekaa Western",
        "Al-Lawz Kamid Bekaa Western","Kawkaba Rachaiya","Kfarzabad Zahle","Qanafar Khirbet Bekaa Western",
        "Rouha Khirbet Rachaiya","Lala Bekaa Western","Lubya Bekaa Western",
        "Taanayel and Maaloula Zahle","Anjar Majdal Zahle","Fadel Bani Majdal Rachaiya",
        "Makse Zahle","Mashgharah Bekaa Western","Massa Zahle","Lussia and Midoun Bekaa Western",
        "Mrayjet Zahle","Mudawwara Rachaiya","Nasiriya Zahle","Niha Zahle","Qilya Bekaa Western",
        "El-Dleim Wadi - Elias Qob Zahle","Qousaya Zahle","Rashaya Rachaiya","Hala Housh - Riak Zahle",
        "Riyat Zahle","Saadnayel Zahle","Saghbin Bekaa Western","Sahmara Bekaa Western",
        "almuahada Ya'qub Sultan Bekaa Western","Talabayya Zahle","Dzanoub Tall Bekaa Western",
        "Tannourine Rachaiya","Trebil Zahle","Yahmar Bekaa Western","Yanta Rachaiya","Zahl", "Others"],
    "Beirut": ["Beirut", "Others"],
    "Mount Lebanon": [
        "Aaaroun Matn",
        "Aaqbiyeh Kesrouane",
        "Achqout Bkaatouta Kesrouane",
        "Ad-Dahr Mazraat Chouf El",
        "Aeroun Matn",
        "Ahmouch Byblos",
        "Ajaltoun Kesrouane",
        "Ainab Aalay",
        "Ainab Chouf El",
        "Ainout Chouf El",
        "Aintoura Kesrouane",
        "Aitryoun Chouf El",
        "Al-Azra Kesrouane",
        "Al-Barajneh Burj Baabda",
        "Al-Barghoutiyya at Mzaira and Aalman Chouf El",
        "Al-Dafnah and Adma Kesrouane",
        "Al-Ghadeer-Al-Lailka Al-Muraijeh-Tahweta Baabda",
        "Al-Ghayneh Kesrouane",
        "Al-Kosiba Baabda",
        "Al-Urbaniyah-Al-Dalibah Baabda",
        "Al-Rehanah Ain Kesrouane",
        "Al-Kosiba Baabda",
        "Al-Ghadeer-Al-Lailka Al-Muraijeh-Tahweta Baabda",
        "Al-Kosiba Baabda",
        "Aqoura Al Byblos",
        "Aramoun Kesrouane",
        "Arsoun Jouret Baabda",
        "Arayya Baabda",
        "Ashqout Kesrouane",
        "Az-Zuweiriyah Chouf El",
        "Badran Jourat Kesrouane",
        "Baabdat Matn",
        "Baadaran Chouf El",
        "Baakline Chouf El",
        "Baassir Chouf El",
        "Ballout El Ruwayset Baabda",
        "Barja Chouf El",
        "Bassaba Chouf El",
        "Batater Aalay",
        "Bater Chouf El",
        "Batgrine Matn",
        "Batha Kesrouane",
        "Baysour Aalay",
        "Bdeghan Aalay",
        "Biknaya - Dib El Jal Matn",
        "Blat-Aoukar Khrab-Haret El Dbayeh-Zouk Matn",
        "Blouneh Kesrouane",
        "Bmariam Baabda",
        "Bneyeh Al Aalay",
        "Bqaatouta Kesrouane",
        "Broumana Matn",
        "Bware Al Kesrouane",
        "Byakout Matn",
        "Bzebdine Baabda",
        "Bzommar Kesrouane",
        "Chabab Beit Matn",
        "Chalhoub Zalka-Ammar Matn",
        "Chanehye Aalay",
        "Charoun Aalay",
        "Chehim Chouf El",
        "Chiyah Baabda",
        "Chouf El Jdeideh Chouf El",
        "Chouf El Maasser Chouf El",
        "Dalbatta Kesrouane",
        "Dalhoun Chouf El",
        "Daisheh Ad-Maklas Al-Mansouriyah Al Matn",
        "Daraya Chouf El",
        "Daroun Kesrouane",
        "Darya Kesrouane",
        "Dawwar Al-Musa Mar Matn",
        "Dawwar Matn",
        "Dfoun Aalay",
        "DoukMakayl Kesrouane",
        "El-Mghara Dahr Chouf El",
        "Faitroun Kesrouane",
        "Fanar Matn",
        "Faraya Kesrouane",
        "Fatqa Kesrouane",
        "Fatri Byblos",
        "Fil el Sin Matn",
        "Furn Baabda",
        "Ghabaleh Kesrouane",
        "Gharife Chouf El",
        "Ghazir Kesrouane",
        "Ghobeiry Baabda",
        "Ghodras Kesrouane",
        "Ghousta Kesrouane",
        "Ghabbah Al Matn",
        "Haouz Al Jewar Baabda",
        "Halat Byblos",
        "Hammana Baabda",
        "Hammoud Bourj Matn",
        "Harf Al Ras Baabda",
        "Harf El Deir Baabda",
        "Harajel Kesrouane",
        "Hasbaya Baabda",
        "Hasin Al Kesrouane",
        "Hasrout Chouf El",
        "Haytah Kesrouane",
        "Hazmieh Baabda",
        "Hreik Haret Baabda",
        "Hilalia Baabda",
        "Houdaira El Mazraat - Chaar El Beit Matn",
        "Ibrahim Nahr Byblos",
        "Jaj Byblos",
        "Jbaa Chouf El",
        "Jbeil Byblos",
        "Jdeideh Kesrouane",
        "Jedra Chouf El",
        "Jiyeh Chouf El",
        "Joueita Kesrouane",
        "Joun Chouf El",
        "Jounieh Kesrouane",
        "Jarif Kfar & Nemoura Kesrouane",
        "Kako El Aar-Beit Chehwan-Ain Qornet Matn",
        "Kaifun Aalay",
        "Karam Al Baabda",
        "Karya Al Baabda",
        "Kfardbian Kesrouane",
        "Kfarmatta Aalay",
        "Kfarselwan Baabda",
        "Kfertay Kesrouane",
        "Kfouar Kesrouane",
        "Khuraibeh Baabda",
        "Kholouniyeh Al Chouf El",
        "Khreibeh Al Chouf El",
        "Lassa Byblos",
        "Majdlaya Aalay",
        "Majdoub Al-Mazraa-Bsallim Matn",
        "Marj al Ain Mansouriya Al Aalay",
        "Matallah Al Chouf El",
        "Mazboud Chouf El",
        "Mazkah Al-Chaaya Mar Matn",
        "Merouba Kesrouane",
        "Meri Beit Matn",
        "Mghayriyeh Chouf El",
        "Mhaid El Jouret W Chehatoal Kesrouane",
        "Mosbeh Zouk Kesrouane",
        "Muhaidatha Al-Bikfaya Matn",
        "Mrayjet & Bourjein Chouf El",
        "Mristi Chouf El",
        "Mukhtara Al Chouf El",
        "Nahr El Tahwitet - Remmaneh El Ain - Chebbak El Furn",
        "Naqash Al-Antelias Matn",
        "Niha Chouf El",
        "Nabiheet Matn",
        "Oyoun Al Matn",
        "Qabi` Baabda",
        "Qartaba Byblos",
        "Qattara Al Mifouk Byblos",
        "Qulayat Al Kesrouane",
        "Rabieh Matn",
        "Rachin Kesrouane",
        "Reefoun Kesrouane",
        "Remhala Aalay",
        "Rmeileh Chouf El",
        "Roumiyeh Matn",
        "Rmeileh Chouf El",
        "Safa Al-Misk-Bahr Saqiyat Matn",
        "Safra Kesrouane",
        "Sahylih Al Kesrouane",
        "salima Baabda",
        "Shabaniya Baabda",
        "Shennaya Kesrouane",
        "Shuwit Baabda",
        "Sibline Chouf El",
        "Smakiah Chouf El",
        "Sofar Aalay",
        "Tabarja Kesrouane",
        "Tarshish Baabda",
        "Tartij Byblos",
        "Wardanieh Chouf El",
        "Yashouh Mazraat Matn",
        "Yahchouch Kesrouane",
        "Zaaitra Kesrouane",
        "Zaytoun Kesrouane", "Others"],
    "North Lebanon": [
        "Aabrin",
        "Aakrine",
        "Aal Mina",
        "Aimar",
        "Ajdabra",
        "Ajdabrin",
        "Al-Badawi",
        "Al-Hazmiyeh",
        "Al-Majdal",
        "Al-Mina",
        "Al-Qalamoun",
        "Al-Safira",
        "Amyoun",
        "Anfeh",
        "Asia",
        "Asoun",
        "Ayal",
        "Baan",
        "Bakhoun",
        "Banshie",
        "Basliqit",
        "Bassirma",
        "Batarmaz",
        "Batram",
        "Batroumine",
        "Bcoza and Namreen",
        "Bazoun",
        "Bchamzin",
        "Bdebba",
        "Bdenaile",
        "Bechtar Dar",
        "Bela Deir",
        "Bkoza and Namreen",
        "Bkrkasha",
        "Bqarsouna",
        "Bqosta",
        "Bshaleh",
        "Bsharri",
        "Btaaboura",
        "Btouratije",
        "Bursa",
        "Bziza",
        "Chatine",
        "Chlala",
        "Chmizzine",
        "Darya-Bishnin",
        "Dede",
        "Douma",
        "Ezaki",
        "Fiyeh",
        "Fawar Al Harat",
        "Hamat",
        "Heri",
        "Hassroun",
        "Izal",
        "Jebbeh El Hadath",
        "Jran",
        "Kaftoun",
        "Kassab Bayt - Hardine",
        "Kfaraarabi",
        "Kfarabida",
        "Kfarahezir",
        "Kfaraka",
        "Kfarbanin",
        "Kfarchi",
        "Kfardfou",
        "Kfardlakos",
        "Kfarhabu",
        "Kfarhata",
        "Kfarhatta",
        "Kfarhelda",
        "Kfarsaroun",
        "Kfaryachit-Bassbaal",
        "Kfraya",
        "Koubba",
        "Kour",
        "Kousba",
        "Majdalia",
        "Markabta",
        "Metrith",
        "Nahash Ras",
        "Qannat",
        "Qolehate",
        "Qorsayta",
        "Rachadbin",
        "Rachiine",
        "Salata",
        "Saraal",
        "Seer",
        "Shaayt Hdad",
        "Shbatin",
        "Tannourine",
        "Taran",
        "Tehoum",
        "Tuffah Al Mazraat",
        "Tourine",
        "Tourza",
        "Tripoli",
        "Zan",
        "Zgharta-Ehden", "Others"],
    "South Lebanon": [
        "Aabra Saida","Aarai Jezzine","Adloun Saida","Adousiyeh Saida","Baal Ain Sour","Eddelb Ain Saida",
        "Abbasiyah Al Sour","Bayyad Al Sour","Bazuriyah Al Sour","Bisariyah Al Saida","Burghliye Al Sour",
        "Bustan Al Sour","Hamiri Al Sour","Hilaliyah Al Saida","Hlousiyeh Al Sour","Jibbin Al Sour",
        "Lubiyah Al Saida","Maknouneh Al Jezzine","Mansouri Al Sour","Marwaniyah Al Saida",
        "Mayy Wal Mayy Al Saida","Midan Al Jezzine","Qulaylah Al Sour","Quryah Al Saida",
        "Sahel Al Malikiyat and Shaatiye Al Sour","Al-Eishiyeh Jezzine","Al-Hamssiyeh Jezzine",
        "Al-Louwayzeh Jezzine","Al-Rayhan Jezzine","Alhinya Sour","Alkanisa Sour","Shaaab Ash Alma Sour",
        "Alzahira Sour","Najariyah An Saida","Naqoura An Sour","Anqoun Saida","Ansariyah Saida",
        "Aramta Jezzine","Arzoun Sour","Aytit Sour","Azour Jezzine","Babliyeh Saida","Baksata Saida",
        "Baramiyeh Saida","Batoulieh Sour","Bedeas Sour","dependencies its and Bkassine Jezzine",
        "Bnouhate Jezzine","Shamali Al Bourj Sour","Abdallah Abou Ain and Rahhal Bourj Sour",
        "Al-Laqch Bteddine Jezzine","Amess Deir Sour","Keifa Deir Sour","Nahr En Qanoun Deir Sour",
        "Ain Al Ras Qanoun Deir Sour","Essim Derb Saida","Dirdghayya Sour","Ghassaniyeh Saida",
        "Ghazieh Saida","Saida Haret Saida","Haytoura Jezzine","Hinawiye Sour","Albutm Jabal Sour",
        "Jannata Sour","Majdeline Ain - Jezzine Jezzine","Jrania Jezzine","Karkha Jezzine",
        "al-Siyad Kawthariyat Saida","Jirra Kfar Jezzine","Kfarfalous Jezzine","Khartoum Saida",
        "Labaa Jezzine","Maaroub Sour","Majadel Sour","Majdal Jezzine","Majdalyoun Saida",
        "Majdalzoun Sour","Marwahine Sour","Moshref Mazraat Sour","Mchmoush", "Others"],
    "Nabatieh": [
        "Aaba",
        "Adchit",
        "Al-Fardis",
        "Al-Fawqa",
        "Al-Gharbiya Sair",
        "Al-Gharbiya Zawtar",
        "Al-Habariyah",
        "Al-Kafr",
        "Al-Khalwat",
        "Al-Sharkiya",
        "Al-Tahta Houmine",
        "Ansar",
        "Arabsalim",
        "Arnoun",
        "Bariqaa",
        "Bridge Kaakaiye",
        "Choukeen",
        "Doueir",
        "Ezza",
        "Fila Kafr",
        "Habbouch",
        "Harouf",
        "Jargea",
        "Jbaa",
        "Jibchit",
        "Kfour",
        "Mayfadoun",
        "Mimas",
        "Nabatieh",
        "Nemriye",
        "Rumine",
        "Ruman Kafr",
        "Sarbah",
        "Seen",
        "Shuba Kafr",
        "Yohmor",
        "Zefta",
        "Zibdeen", "Others"]
}

@app.route('/', methods=['GET', 'POST'])
def index():
    submitted_data = None
    if request.method == 'POST':
        submitted_data = request.form.to_dict(flat=False)
    return render_template_string(
        form_html,
        skills_list=skills_list,
        categories=unique_sorted([s['category_name'] for s in skills_list]),
        subcategories=unique_sorted([s['subcategory_name'] for s in skills_list]),
        municipalities_json=json.dumps(municipalities),  # <-- fix here
        data=submitted_data
    )
@app.route("/get_api_skills", methods=["POST"])
def get_api_skills():
    data = request.get_json()
    title = data.get("job_title")

    import requests

    payload = {
        "job_title": title,
        "country": "Lebanon"
    }

    r = requests.post("https://skillsmonitor.unescwa.org/api/getProfile", json=payload)
    res = r.json()

    hard = [s["name"] for s in res["data"]["hard_skills"]["schema"]]
    soft = [s["name"] for s in res["data"]["soft_skills"]["schema"]]

    return jsonify({"skills": hard + soft})
@app.route("/extract_from_text", methods=["POST"])
def extract_from_text():
    from Emsi import extract_skills_from_text

    # Use the JSON 'text' if provided
    text = request.get_json().get("text", "")

    # Extract skills
    skills_dict = extract_skills_from_text(text)

    # Combine hard + soft skills into a list
    skills = []
    if skills_dict.get("hard_skills"):
        skills += [s.strip() for s in skills_dict["hard_skills"].split(",") if s.strip()]
    if skills_dict.get("soft_skills"):
        skills += [s.strip() for s in skills_dict["soft_skills"].split(",") if s.strip()]

    return jsonify({"skills": skills})  # Now skills is an array

@app.route('/search_title')
def search_title():
    q = request.args.get('q', '').lower()
    suggestions = [t for t in titles_list if q in t.lower()][:10]
    return jsonify(suggestions)


@app.route("/extract_skills", methods=["POST"])
def extract_skills_api():
    data = request.get_json()
    text = data.get("text", "")
    # افترض extract_skills_from_text يعيد dict مثل {'hard_skills': [...], 'soft_skills': [...]}
    extracted = extract_skills_from_text(text)
    if not isinstance(extracted, dict):
        return jsonify({"error": "extract_skills_from_text returned unexpected format"}), 500
    return jsonify(extracted)

# ==============================
# Run App
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)

