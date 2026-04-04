# ========================================
# SCORE MODULE CONSTANTS
# ========================================

TIER_THRESHOLDS = {
    'A+': 95, 'A': 90, 'A-': 85,
    'B+': 80, 'B': 75, 'B-': 70,
    'C+': 65, 'C': 60, 'C-': 55,
    'D': 50, 'F': 0
}

MA_CRIME_SEVERITY_WEIGHTS = {
    # Massachusetts Crime Categories
    'Murder and Nonnegligent Manslaughter': 5,
    'Aggravated Assault': 5,
    'Robbery': 5,
    'Statutory Rape': 5,
    'Rape': 5,
    'Sodomy': 5,
    'Criminal Sexual Contact': 5,
    'Incest': 5,
    'Human Trafficking, Commercial Sex Acts': 5,
    'Human Trafficking, Involuntary Servitude': 5,
    'Negligent Manslaughter': 5,
    'Kidnapping/Abduction': 5,

    'Burglary/Breaking & Entering': 3,
    'Motor Vehicle Theft': 3,
    'Simple Assault': 3,
    'Arson': 3,
    'Weapon Law Violations': 3,
    'Animal Cruelty': 3,
    'Purse-snatching': 3,

    'Driving Under the Influence': 1,
    'Disorderly Conduct': 1,
    'Drug/Narcotic Violations': 1,
    'Trespass of Real Property': 1,
    'Stolen Property Offenses': 1,
    'Counterfeiting/Forgery': 1,
    'Credit Card/Automatic Teller Fraud': 1,
    'All Other Larceny': 1,
    'Destruction/Damage/Vandalism of Property': 1,    
    'Theft From Building': 1,
    'Theft From Motor Vehicle': 1,
    'Theft of Motor Vehicle Parts/Accessories': 1,
    'Pocket-picking': 1,
    'Drug Equipment Violations': 1,
    'Impersonation': 1,
}
