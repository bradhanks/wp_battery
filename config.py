

# config.py

# --- Main Configuration ---
# List of domains to be analyzed by the script.
DOMAINS_TO_SCAN = [
    "advanceddentalquincy.com", "ariaperio.com", "berkeleyperioimplants.com",
    "berkshireperio.com", "bigskysmilesandsedation.com", "biologicalcenterfordentistry.com",
    "bluegrassdentistry.com", "brewerdentistry.com", "campcreekdental.com",
    "canyonridgeperio.com", "cardinalparkfamilydental.com", "castlepinesdentalcare.com",
    "centerformoderndentistry.com", "cliffsideparkdental.com", "clovisfamilydentistry.com",
    "codelli-perio.com", "connecticutperiodontist.com", "cook-perio.com",
    "cornerstoneperio.com", "creekwooddentalarts.com", "dentalartcare.com",
    "dentalimplantsandoralsurgery.com", "dentalimplantsofocala.com", "dentalstarz.com",
    "dentistofcharleston.com", "dentistrybydesignmwc.com", "eastmanonline.com",
    "forsythperioimplants.com", "friscoapneaandsnoringtreatment.com", "garhardtdds.com",
    "genuinesmilespa.com", "gloucesterdental.com", "gracedental.org",
    "greatlakesperio.com", "hopkinsdentalclinic.com", "idahofallsidahodentist.com",
    "idahoperio.com", "implants4all.com", "iriedental.com",
    "johnsavukinasdds.com", "keydentalgrp.com", "lakeviewdentistry.com",
    "laneoralsurgery.com", "lastingdentistry.com", "leedydental.com",
    "lexingtonparkdentist.com", "lutzendo.com", "majordentalclinics.com",
    "michiganimplantcenter.com", "middletennesseeperio.com", "midwestoms.com",
    "morganhillsmiles.com", "nashvilleperio.com", "noahsmilegroup.com",
    "northbostonoralsurgery.com", "northbostonoralsurgerygroup.com", "novaperiohealth.com",
    "nwaperio.com", "oralsurgerytexas.com", "palmharbordentistry.com",
    "perio-implant.com", "periodentalimplants.com", "periodontalcenters.com",
    "periodontalmedicine.org", "perioimplantsnyc.com", "pidentists.com",
    "pinnacleperio.com", "premierimplantcenters.com", "progressivedental.com",
    "puredentalgroup.com", "qdentalclinic.com", "redrockperio.com",
    "reimelsdentistry.com", "remmersdental.com", "revolutiondentalimplants.com",
    "richmondsmile.com", "robertfranklindmd.com", "rochesterperio.com",
    "scarsdalepersonaldentalcare.com", "sccdentalcare.com", "serafinfamilydentistry.com",
    "sitwelldental.com", "sloanslakedental.com", "southbeachsmiles.com",
    "sparacinoperio.com", "spartadental.com", "specialistsimplantcenter.com",
    "ssdgsmiles.com", "stmarkspainlessdental.com", "subkadds.com",
    "sundanceimplant.com", "thefalmouthdentist.com", "thewallingforddentist.com",
    "unionimplants.com", "unitedimplantdentistryny.com", "universaldentistry.net",
    "vicksburgdentist.com", "westshoredentistryfl.com", "whiteridgedental.com",
    "williamsportoms.com", "willmardentist.com", "winterstreetdental.com",
    "wolfydentalgroup.com", "yousmiledental.com", "yousmileimplantcenter.com"
]

# --- Technical Settings ---
MAX_WORKERS = 10
REQUEST_TIMEOUT = 20
DB_NAME = "site_analysis_results.db"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
