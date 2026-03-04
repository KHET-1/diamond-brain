#!/usr/bin/env python3
"""
================================================================================
  ARIZONA CRIMINAL LAW SEEDER — Diamond Brain
================================================================================
  Seeds the Diamond Brain with comprehensive Arizona Revised Statutes (ARS)
  relevant to criminal court trials. Covers Title 13 Criminal Code,
  constitutional rights, sentencing, rules of evidence, and rules of
  criminal procedure.

  Usage:
      python seed_ars_criminal.py              # Seed all ARS citations
      python seed_ars_criminal.py --dry-run    # Preview without writing
      python seed_ars_criminal.py --stats      # Show post-seed statistics

  Sources: Arizona Revised Statutes (azleg.gov), Arizona Constitution,
           Arizona Rules of Evidence, Arizona Rules of Criminal Procedure.

  DISCLAIMER: This is a legal research aid, not legal advice. Statutes
  are summarized from publicly codified law. Always verify against the
  current official text at azleg.gov for court use.
================================================================================
"""

import sys
from pathlib import Path

# Ensure brain module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from brain.diamond_brain import DiamondBrain


# ============================================================================
# ARIZONA CRIMINAL LAW CITATIONS
# ============================================================================
# Each entry is a dict matching brain.cite() parameters:
#   code, title, text, category, jurisdiction, severity, source
#
# Categories: statute, procedural, constitutional, evidence-rule
# Severity:   FELONY, MISDEMEANOR, REFERENCE, CONSTITUTIONAL, PROCEDURAL
# ============================================================================

ARS_CITATIONS = [

    # ========================================================================
    # TITLE 13, CHAPTER 1 — GENERAL PROVISIONS
    # ========================================================================
    {
        "code": "ARS 13-105",
        "title": "Definitions",
        "text": (
            "ARS 13-105 provides statutory definitions for terms used throughout "
            "Title 13 (Criminal Code). Key definitions include: "
            "'Conduct' means an act or omission and its accompanying culpable mental state. "
            "'Crime' means a misdemeanor or a felony. "
            "'Culpable mental state' means intentionally, knowingly, recklessly, or with "
            "criminal negligence as defined in ARS 13-105(10). "
            "'Dangerous instrument' means anything that under the circumstances in which "
            "it is used, attempted to be used, or threatened to be used is readily capable "
            "of causing death or serious physical injury. "
            "'Dangerous offense' means an offense involving the discharge, use, or "
            "threatening exhibition of a deadly weapon or dangerous instrument, or the "
            "intentional or knowing infliction of serious physical injury. "
            "'Deadly physical force' means force that is used with the purpose of causing "
            "death or serious physical injury or in the manner of its use or intended use "
            "is capable of creating a substantial risk of causing death or serious "
            "physical injury. "
            "'Deadly weapon' means anything designed for lethal use, including a firearm. "
            "'Felony' means an offense for which a sentence to a term of imprisonment in "
            "the custody of the state department of corrections is authorized. "
            "'Knowingly' means with awareness that conduct is of a prohibited nature or "
            "that a circumstance exists; does not require knowledge of the illegality. "
            "'Intentionally' or 'with the intent to' means a person's objective is to "
            "cause that result or engage in that conduct. "
            "'Recklessly' means a person is aware of and consciously disregards a "
            "substantial and unjustifiable risk that the result will occur or the "
            "circumstance exists; the risk must be of such nature and degree that "
            "disregard constitutes a gross deviation from the standard of conduct a "
            "reasonable person would observe. "
            "'Criminal negligence' means a person fails to perceive a substantial and "
            "unjustifiable risk that the result will occur or the circumstance exists; "
            "the risk must be of such nature and degree that the failure to perceive it "
            "constitutes a gross deviation from the standard of care a reasonable person "
            "would observe. "
            "'Physical injury' means the impairment of physical condition. "
            "'Serious physical injury' includes physical injury that creates a "
            "reasonable risk of death, or that causes serious and permanent "
            "disfigurement, serious impairment of health, or loss or protracted "
            "impairment of the function of any bodily organ or limb. "
            "'Person' means a human being and, as the context requires, an enterprise. "
            "'Possess' means knowingly to have physical possession or otherwise to "
            "exercise dominion or control over property. "
            "'Vehicle' means a device in, on, or by which any person or property is, "
            "may be, or could have been transported or drawn on a public highway, "
            "excluding devices moved by human power or used exclusively on stationary "
            "rails or tracks."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 1",
    },
    {
        "code": "ARS 13-106",
        "title": "Time Limitations",
        "text": (
            "ARS 13-106 establishes the statute of limitations for criminal "
            "prosecutions in Arizona. (A) A prosecution for any homicide, any offense "
            "that is listed in chapter 14 (sexual offenses) or section 13-3212 "
            "(child prostitution), any misuse of public monies, or any felony "
            "involving a minor under 15 years of age may be commenced at any time "
            "(no statute of limitations). (B) Except as provided in subsection A, "
            "prosecutions for other offenses must be commenced within the following "
            "periods after actual discovery of the offense or after discovery should "
            "have occurred with reasonable diligence, whichever first occurs: "
            "(1) For a class 2 through class 6 felony: seven years. "
            "(2) For a misdemeanor: one year. "
            "(3) For a petty offense: six months. "
            "(C) A prosecution is commenced when an indictment, information, or "
            "complaint is filed. "
            "(D) The period of limitation does not run during any time when the "
            "accused is absent from the state or has no reasonably ascertainable "
            "place of abode within the state. "
            "(E) The period of limitation does not run for a felony during any "
            "time when a prosecution for the same conduct is pending in this state."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 1",
    },

    # ========================================================================
    # TITLE 13, CHAPTER 2 — JUSTIFICATION
    # ========================================================================
    {
        "code": "ARS 13-404",
        "title": "Justification — Self-Defense",
        "text": (
            "ARS 13-404 (Justification; self-defense). (A) Except as provided in "
            "subsection B of this section, a person is justified in threatening or "
            "using physical force against another when and to the extent a reasonable "
            "person would believe that physical force is immediately necessary to "
            "protect himself against the other's use or attempted use of unlawful "
            "physical force. (B) A person may not use physical force to resist an "
            "arrest that the person knows or should know is being made by a peace "
            "officer or by a person acting in a peace officer's presence and at the "
            "officer's direction, whether the arrest is lawful or unlawful, unless "
            "the physical force used by the peace officer exceeds that allowed by law. "
            "(C) A person is not required to retreat before threatening or using "
            "physical force under this section. Arizona is a 'stand your ground' "
            "state — there is no duty to retreat before using justified force in "
            "self-defense."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 4 (Justification)",
    },
    {
        "code": "ARS 13-405",
        "title": "Justification — Use of Deadly Physical Force",
        "text": (
            "ARS 13-405 (Justification; use of deadly physical force). A person is "
            "justified in threatening or using deadly physical force against another: "
            "(1) If such person would be justified in threatening or using physical "
            "force against the other under section 13-404, AND (2) when and to the "
            "degree a reasonable person would believe that deadly physical force is "
            "immediately necessary to protect himself against the other's use or "
            "attempted use of unlawful deadly physical force. A person has no duty "
            "to retreat before threatening or using deadly physical force pursuant "
            "to this section if the person is in a place where the person may "
            "legally be and is not engaged in an unlawful act."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 4 (Justification)",
    },
    {
        "code": "ARS 13-406",
        "title": "Justification — Defense of a Third Person",
        "text": (
            "ARS 13-406 (Justification; defense of a third person). A person is "
            "justified in threatening or using physical force or deadly physical "
            "force against another to protect a third person if, under the "
            "circumstances as a reasonable person would believe them to be, such "
            "person would be justified under section 13-404 or 13-405 in threatening "
            "or using physical force or deadly physical force to protect himself "
            "against the unlawful physical force or deadly physical force a "
            "reasonable person would believe is threatening the third person he "
            "seeks to protect. The defender steps into the shoes of the person "
            "being defended and must meet the same reasonable-person standard."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 4 (Justification)",
    },
    {
        "code": "ARS 13-407",
        "title": "Justification — Use of Force in Defense of Premises",
        "text": (
            "ARS 13-407 (Justification; use of physical force in defense of "
            "premises). A person or his agent in lawful possession or control of "
            "premises is justified in threatening to use deadly physical force or "
            "in threatening or using physical force against another when and to the "
            "extent that a reasonable person would believe it immediately necessary "
            "to prevent or terminate the commission or attempted commission of a "
            "criminal trespass by the other person in or upon the premises. A person "
            "may use deadly physical force under subsection A only in the defense "
            "of himself or third persons as described in sections 13-405 and 13-406. "
            "Note: This section covers non-residential premises such as businesses "
            "and land; residential defense is primarily covered under 13-411 "
            "(Castle Doctrine)."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 4 (Justification)",
    },
    {
        "code": "ARS 13-408",
        "title": "Justification — Use of Force in Crime Prevention",
        "text": (
            "ARS 13-408 (Justification; use of physical force in crime prevention). "
            "A person is justified in threatening or using physical force against "
            "another when and to the extent a reasonable person would believe that "
            "physical force is immediately necessary to prevent what a reasonable "
            "person would believe is an attempt to commit theft, criminal damage, "
            "or any felony involving physical force or threat of physical force. A "
            "person may use deadly physical force under subsection A only if a "
            "reasonable person would believe it necessary to prevent the commission "
            "of arson of an occupied structure under section 13-1704, burglary in "
            "the second or first degree under section 13-1507 or 13-1508, kidnapping "
            "under section 13-1304, manslaughter under section 13-1103, second or "
            "first degree murder under section 13-1104 or 13-1105, sexual conduct "
            "with a minor under section 13-1405, sexual assault under section "
            "13-1406, child molestation under section 13-1410, armed robbery under "
            "section 13-1904, or aggravated assault under section 13-1204(A)(1) or "
            "(A)(2)."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 4 (Justification)",
    },
    {
        "code": "ARS 13-411",
        "title": "Justification — Use of Force in Defense of Residential Structure (Castle Doctrine)",
        "text": (
            "ARS 13-411 (Justification; use of force in defense of a residential "
            "structure or occupied vehicle; definition). (A) A person is justified "
            "in threatening to use or using physical force or deadly physical force "
            "against another person if and to the extent the person reasonably "
            "believes that physical force or deadly physical force is immediately "
            "necessary to prevent the other person's commission of arson of an "
            "occupied structure under section 13-1704, burglary in the second or "
            "first degree under section 13-1507 or 13-1508, kidnapping under "
            "section 13-1304, or any felony offense under chapter 11 of this title "
            "(sexual offenses) involving the threatened or actual use of force. "
            "(B) There is no duty to retreat before threatening to use or using "
            "physical force or deadly physical force justified by subsection A. "
            "(C) A person is presumed to be acting reasonably for purposes of this "
            "section if the person is acting to prevent what the person reasonably "
            "believes is the imminent commission of any of the offenses listed in "
            "subsection A. "
            "(D) 'Residential structure' means any dwelling, whether occupied or "
            "not, including mobile homes, manufactured homes, and any attached "
            "porch. This is Arizona's Castle Doctrine — it creates a presumption "
            "of reasonableness when defending one's home or occupied vehicle against "
            "forcible entry crimes."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 4 (Justification)",
    },

    # ========================================================================
    # TITLE 13, CHAPTER 4 — OFFENSES AGAINST PROPERTY
    # ========================================================================
    {
        "code": "ARS 13-1802",
        "title": "Theft",
        "text": (
            "ARS 13-1802 (Theft). A person commits theft if, without lawful "
            "authority, the person knowingly: (1) Controls property of another "
            "with the intent to deprive the other person of such property; or "
            "(2) Converts for an unauthorized term or use services or property "
            "of another entrusted to the defendant or placed in the defendant's "
            "possession for a limited, authorized term or use; or "
            "(3) Obtains services or property of another by means of any material "
            "misrepresentation with intent to deprive the other person of such "
            "property or services; or "
            "(4) Comes into control of lost, mislaid, or misdelivered property "
            "under circumstances providing means of inquiry as to the true owner "
            "and appropriates such property without reasonable efforts to notify "
            "the true owner; or "
            "(5) Controls property of another knowing or having reason to know "
            "that the property was stolen; or "
            "(6) Obtains services known to the defendant to be available only "
            "for compensation without paying or an agreement to pay. "
            "Classification: Theft of property/services valued at $25,000 or more "
            "is a class 2 felony. $4,000-$25,000 is a class 3 felony. $3,000-$4,000 "
            "is a class 4 felony. $2,000-$3,000 is a class 5 felony. $1,000-$2,000 "
            "is a class 6 felony. Less than $1,000 is a class 1 misdemeanor. "
            "Theft of a firearm or an animal taken for the purpose of animal "
            "fighting is a class 6 felony regardless of value."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 18",
    },
    {
        "code": "ARS 13-1805",
        "title": "Shoplifting",
        "text": (
            "ARS 13-1805 (Shoplifting). A person commits shoplifting if, while in "
            "an establishment in which merchandise is displayed for sale, the person "
            "knowingly obtains such goods by any of the following: (1) Removing "
            "goods from the immediate display or from any other place within the "
            "establishment without paying the purchase price; (2) Charging the "
            "purchase price to a fictitious person or without the authority of the "
            "actual account holder; (3) Paying less than the purchase price by means "
            "of altering, removing, or disfiguring any label, price tag, or marking; "
            "(4) Transferring goods from one container to another; (5) Concealment. "
            "Classification: Shoplifting property valued at $2,000 or more is a "
            "class 5 felony. Shoplifting property valued at $1,000-$2,000 is a "
            "class 6 felony. Less than $1,000 is a class 1 misdemeanor. "
            "Shoplifting using an artifice, instrument, container, device, or other "
            "article to facilitate the shoplifting is a class 5 felony regardless of "
            "the value. Shoplifting in concert with one or more other persons "
            "is a class 5 felony regardless of value. A third or subsequent "
            "shoplifting offense within a period of five years is a class 4 felony "
            "regardless of value (ARS 13-1805(I))."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 18",
    },

    # ========================================================================
    # TITLE 13, CHAPTER 5 — OFFENSES AGAINST PERSONS (Homicide)
    # ========================================================================
    {
        "code": "ARS 13-1102",
        "title": "Negligent Homicide",
        "text": (
            "ARS 13-1102 (Negligent homicide). (A) A person commits negligent "
            "homicide if with criminal negligence the person causes the death of "
            "another person, including an unborn child at any stage of its "
            "development. (B) An offense under this section applies to an unborn "
            "child at any stage of its development. A person shall not be "
            "prosecuted under this section if the person was performing an abortion "
            "for which the consent of the pregnant woman was obtained or if the "
            "pregnant woman herself committed the act. "
            "Classification: Negligent homicide is a class 4 felony. "
            "The culpable mental state is 'criminal negligence' — a failure to "
            "perceive a substantial and unjustifiable risk that constitutes a "
            "gross deviation from the standard of care a reasonable person would "
            "observe. Presumptive sentence for a first offense: 2.5 years."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 11",
    },
    {
        "code": "ARS 13-1103",
        "title": "Manslaughter",
        "text": (
            "ARS 13-1103 (Manslaughter). A person commits manslaughter by: "
            "(1) Recklessly causing the death of another person; or "
            "(2) Committing second degree murder as defined in section 13-1104(A)(3) "
            "upon a sudden quarrel or heat of passion resulting from adequate "
            "provocation by the victim; or "
            "(3) Intentionally providing the physical means that another person uses "
            "to commit suicide, with the knowledge that the person intends to commit "
            "suicide; or "
            "(4) Committing second degree murder as defined in section 13-1104(A)(1) "
            "or (A)(2) while being coerced to do so by the use or threatened "
            "immediate use of unlawful deadly physical force upon such person or a "
            "third person which a reasonable person in his situation would have been "
            "unable to resist; or "
            "(5) Knowingly or recklessly causing the death of an unborn child at any "
            "stage of its development by any physical injury to the mother. "
            "Classification: Manslaughter is a class 2 felony. If the victim is "
            "an unborn child, it is a class 2 felony. Presumptive sentence for a "
            "non-dangerous first offense: 5 years (range: 3 to 12.5 years). "
            "Note: Manslaughter subsection (2) is often called 'voluntary "
            "manslaughter' or 'heat of passion' — it mitigates what would "
            "otherwise be second degree murder."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 11",
    },
    {
        "code": "ARS 13-1104",
        "title": "Second Degree Murder",
        "text": (
            "ARS 13-1104 (Second degree murder). (A) A person commits second degree "
            "murder if without premeditation: "
            "(1) The person intentionally causes the death of another person, "
            "including an unborn child; or "
            "(2) Knowing that the person's conduct will cause death or serious "
            "physical injury, the person causes the death of another person, "
            "including an unborn child; or "
            "(3) Under circumstances manifesting extreme indifference to human life, "
            "the person recklessly engages in conduct that creates a grave risk of "
            "death and thereby causes the death of another person, including an "
            "unborn child. "
            "Classification: Second degree murder is a class 1 felony. "
            "Sentencing: The presumptive term is 10.5 years for non-dangerous "
            "offenders (range: 7 to 21 years). For dangerous offenses (involving "
            "deadly weapon or dangerous instrument): presumptive 15.75 years "
            "(range: 10.5 to 21 years). "
            "Key distinction from first degree murder: second degree murder lacks "
            "premeditation. Key distinction from manslaughter: second degree murder "
            "requires intentional or knowing conduct, or extreme recklessness, "
            "whereas manslaughter requires only recklessness or heat of passion."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 11",
    },
    {
        "code": "ARS 13-1105",
        "title": "First Degree Murder",
        "text": (
            "ARS 13-1105 (First degree murder). A person commits first degree "
            "murder if: "
            "(1) Intending or knowing that the person's conduct will cause death, "
            "the person causes the death of another person, including an unborn "
            "child, with premeditation; or "
            "(2) Acting either alone or with one or more other persons the person "
            "commits or attempts to commit any of the following predicate felonies "
            "and in the course of and in furtherance of the offense or immediate "
            "flight from the offense, the person or another person causes the "
            "death of any person (felony murder): sexual conduct with a minor "
            "(13-1405), sexual assault (13-1406), molestation of a child (13-1410), "
            "terrorism (13-2308.01), marijuana offenses (13-3405(A)(4) involving "
            "distribution), dangerous drug offenses (13-3407(A)(4) involving "
            "distribution), narcotic drug offenses (13-3408(A)(7) involving "
            "distribution), drive-by shooting (13-1209), kidnapping (13-1304), "
            "burglary first or second degree (13-1507, 13-1508), arson of occupied "
            "structure (13-1704), robbery (13-1902), armed robbery (13-1904), or "
            "unlawful flight from law enforcement (28-622.01). "
            "Classification: First degree murder is a class 1 felony punishable "
            "by death, natural life, or life with the possibility of release "
            "after 25 years (35 years if the victim was under 15). "
            "Premeditation: The state must prove the defendant acted with "
            "premeditation, meaning the defendant intended to kill and the "
            "intention was the result of actual reflection, not merely a "
            "spontaneous act. Premeditation may be instantaneous — it requires "
            "reflection, not a specific duration of time."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 11",
    },

    # ========================================================================
    # TITLE 13, CHAPTER 5 — OFFENSES AGAINST PERSONS (Assault)
    # ========================================================================
    {
        "code": "ARS 13-1203",
        "title": "Assault",
        "text": (
            "ARS 13-1203 (Assault). (A) A person commits assault by: "
            "(1) Intentionally, knowingly, or recklessly causing any physical "
            "injury to another person; or "
            "(2) Intentionally placing another person in reasonable apprehension "
            "of imminent physical injury; or "
            "(3) Knowingly touching another person with the intent to injure, "
            "insult, or provoke such person. "
            "Classification: "
            "Assault committed by intentionally, knowingly, or recklessly causing "
            "physical injury (subsection 1) is a class 1 misdemeanor. "
            "Assault by placing another in reasonable apprehension of imminent "
            "physical injury (subsection 2) is a class 2 misdemeanor. "
            "Assault by knowingly touching to injure, insult, or provoke "
            "(subsection 3) is a class 3 misdemeanor. "
            "Maximum penalties: Class 1 misdemeanor — up to 6 months jail and "
            "$2,500 fine. Class 2 — up to 4 months and $750. Class 3 — up to "
            "30 days and $500."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "MISDEMEANOR",
        "source": "ARS Title 13, Ch. 12",
    },
    {
        "code": "ARS 13-1204",
        "title": "Aggravated Assault",
        "text": (
            "ARS 13-1204 (Aggravated assault). A person commits aggravated assault "
            "if the person commits assault as defined in section 13-1203 under any "
            "of the following circumstances: "
            "(A)(1) If the person causes serious physical injury to another; "
            "(A)(2) If the person uses a deadly weapon or dangerous instrument; "
            "(A)(3) If the person commits the assault by any means of force that "
            "causes temporary but substantial disfigurement, temporary but "
            "substantial loss or impairment of any body organ or part, or a "
            "fracture of any body part; "
            "(A)(4) If the person commits the assault while the victim is bound "
            "or otherwise physically restrained or while the victim's capacity to "
            "resist is substantially impaired; "
            "(A)(5) If the person commits the assault after entering the private "
            "home of another with the intent to commit the assault; "
            "(A)(6) If the person is eighteen years of age or older and commits "
            "the assault upon a child who is fifteen years of age or under; "
            "(A)(7) If the person commits assault upon a peace officer, firefighter, "
            "teacher, health care practitioner, or prosecutor while they are engaged "
            "in official duties; "
            "(A)(8) If the person uses a simulated deadly weapon; "
            "(A)(9)-(A)(11) Additional aggravating factors including assault on "
            "correctional officers, assault involving order of protection violation, "
            "and assault on a person in their vehicle. "
            "Classification: Ranges from class 2 to class 6 felony depending on "
            "the specific subsection. Aggravated assault causing serious physical "
            "injury is a class 3 felony. With a deadly weapon is a class 3 felony "
            "and is automatically a 'dangerous offense' with mandatory prison. "
            "Against a peace officer is a class 5 felony (class 3 if serious "
            "physical injury results). "
            "Dangerous offense designation: Subsections (A)(1) and (A)(2) are "
            "almost always classified as 'dangerous offenses' under ARS 13-105, "
            "triggering mandatory prison under ARS 13-704."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 12",
    },

    # ========================================================================
    # TITLE 13, CHAPTER 6 — DRUG OFFENSES (Title 13, Chapter 34)
    # ========================================================================
    {
        "code": "ARS 13-3401",
        "title": "Drug Definitions",
        "text": (
            "ARS 13-3401 (Definitions — Drug offenses). Key definitions for "
            "Arizona drug law: "
            "'Dangerous drug' means a drug or its salts defined in ARS 13-3401(6), "
            "including methamphetamine, amphetamine, LSD, PCP, MDMA (ecstasy), "
            "psilocybin, GHB, ketamine, anabolic steroids, and numerous synthetic "
            "substances. The full list is extensive and updated by the legislature. "
            "'Drug paraphernalia' means all equipment, products, and materials of "
            "any kind that are used, intended for use, or designed for use in "
            "planting, propagating, cultivating, growing, harvesting, manufacturing, "
            "compounding, converting, producing, processing, preparing, testing, "
            "analyzing, packaging, repackaging, storing, containing, concealing, "
            "injecting, ingesting, inhaling, or otherwise introducing into the "
            "human body a drug in violation of this chapter. "
            "'Manufacture' means the production, preparation, propagation, "
            "compounding, mixing, or processing of a drug, directly or indirectly. "
            "'Marijuana' means all parts of any plant of the genus cannabis, "
            "whether growing or not, and the seeds of such plant (subject to "
            "Proposition 207 / Smart and Safe Arizona Act exceptions). "
            "'Narcotic drug' means coca leaves, opium, heroin, fentanyl, "
            "oxycodone, morphine, codeine, hydrocodone, methadone, and their "
            "derivatives and analogues. "
            "'Threshold amount' means the statutory quantity above which there "
            "is a presumption of possession for sale rather than personal use. "
            "These thresholds vary by substance (e.g., 2 lbs marijuana, 9 grams "
            "cocaine, 1 gram heroin, 4 grams/50 ml PCP, 9 grams methamphetamine, "
            "9 grams amphetamine)."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 34",
    },
    {
        "code": "ARS 13-3405",
        "title": "Possession, Use, Sale, or Transfer of Marijuana",
        "text": (
            "ARS 13-3405 (Possession, use, production, sale, or transportation of "
            "marijuana). NOTE: Proposition 207 (Smart and Safe Arizona Act, effective "
            "2020) legalized recreational marijuana possession of up to one ounce "
            "(5 grams concentrate) for adults 21+ and allows home cultivation of up "
            "to 6 plants. The criminal provisions below apply to conduct OUTSIDE "
            "Prop 207 allowances. "
            "(A) A person shall not knowingly: "
            "(1) Possess or use marijuana; "
            "(2) Possess marijuana for sale; "
            "(3) Produce marijuana; "
            "(4) Transport for sale, import, sell, transfer, or offer to sell or "
            "transfer marijuana. "
            "Classification (for amounts exceeding Prop 207 limits or unlicensed "
            "activity): "
            "Possession/use of less than 2 lbs is a class 6 felony. "
            "Possession for sale of less than 2 lbs is a class 4 felony. "
            "Production of less than 2 lbs is a class 5 felony. "
            "Sale/transport for sale of less than 2 lbs is a class 3 felony. "
            "Amounts of 2 lbs or more increase classification (up to class 2 felony "
            "for sale of 2+ lbs). "
            "Prop 207 note: First-time possession of amounts slightly over the "
            "legal limit (over 1 oz but under 2.5 oz) is a petty offense with a "
            "maximum $300 fine, not a felony."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 34",
    },
    {
        "code": "ARS 13-3407",
        "title": "Possession, Use, Sale, or Transfer of Dangerous Drugs",
        "text": (
            "ARS 13-3407 (Possession, use, administration, acquisition, sale, "
            "manufacture, or transportation of dangerous drugs). "
            "(A) A person shall not knowingly: "
            "(1) Possess or use a dangerous drug; "
            "(2) Possess a dangerous drug for sale; "
            "(3) Possess equipment or chemicals for the purpose of manufacturing "
            "a dangerous drug; "
            "(4) Manufacture a dangerous drug; "
            "(5) Administer a dangerous drug to another person; "
            "(6) Obtain or procure the administration of a dangerous drug by "
            "fraud, deceit, misrepresentation, or subterfuge; "
            "(7) Transport for sale, import, sell, transfer, or offer to sell "
            "or transfer a dangerous drug. "
            "Classification: "
            "Possession/use is a class 4 felony. "
            "Possession for sale is a class 2 felony. "
            "Manufacturing is a class 2 felony. "
            "Sale/transport for sale is a class 2 felony. "
            "For methamphetamine specifically: possession of any amount is a "
            "class 4 felony; possession for sale is a class 2 felony with "
            "presumptive 5 years (range 3-12.5). "
            "Threshold amounts trigger presumption of possession for sale: "
            "9 grams methamphetamine/amphetamine, 9 doses LSD, 2 lbs marijuana."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 34",
    },
    {
        "code": "ARS 13-3408",
        "title": "Possession, Use, Sale, or Transfer of Narcotic Drugs",
        "text": (
            "ARS 13-3408 (Possession, use, administration, acquisition, sale, "
            "manufacture, or transportation of narcotic drugs). "
            "(A) A person shall not knowingly: "
            "(1) Possess or use a narcotic drug; "
            "(2) Possess a narcotic drug for sale; "
            "(3) Possess equipment or chemicals for the purpose of manufacturing "
            "a narcotic drug; "
            "(4) Manufacture a narcotic drug; "
            "(5) Administer a narcotic drug to another person; "
            "(6) Obtain or procure the administration of a narcotic drug by fraud; "
            "(7) Transport for sale, import, sell, transfer, or offer to sell "
            "or transfer a narcotic drug. "
            "Classification: "
            "Possession/use is a class 4 felony. "
            "Possession for sale is a class 2 felony. "
            "Manufacturing is a class 2 felony. "
            "Sale/transport for sale is a class 2 felony. "
            "Narcotic drugs include heroin, fentanyl, cocaine, oxycodone, "
            "morphine, and their derivatives. "
            "Threshold amounts for presumption of sale: 1 gram heroin, 9 grams "
            "cocaine, 750 mg cocaine base (crack). "
            "Fentanyl enforcement: Arizona has aggressively prosecuted fentanyl "
            "cases; possession of any amount of fentanyl is a class 4 felony, "
            "and sale/distribution can be charged as a class 2 felony with "
            "dangerous offense enhancement. Sale of fentanyl resulting in death "
            "can support first degree murder charges under the felony murder rule "
            "(ARS 13-1105(A)(2))."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 34",
    },

    # ========================================================================
    # TITLE 28 — DUI / TRAFFIC OFFENSES
    # ========================================================================
    {
        "code": "ARS 28-1381",
        "title": "Driving Under the Influence (DUI)",
        "text": (
            "ARS 28-1381 (Driving or actual physical control while under the "
            "influence). (A) It is unlawful for a person to drive or be in actual "
            "physical control of a vehicle in this state under any of the "
            "following circumstances: "
            "(1) While under the influence of intoxicating liquor, any drug, a "
            "vapor releasing substance containing a toxic substance, or any "
            "combination of liquor, drugs, or vapor releasing substances if the "
            "person is impaired to the slightest degree; "
            "(2) If the person has an alcohol concentration of 0.08 or more "
            "within two hours of driving or being in actual physical control "
            "of the vehicle and the alcohol concentration results from alcohol "
            "consumed either before or while driving or being in actual physical "
            "control of the vehicle; "
            "(3) While there is any drug defined in section 13-3401 or its "
            "metabolite in the person's body (except if the person holds a valid "
            "prescription for the drug and is using it as directed, or if the "
            "metabolite is from marijuana and the person holds a valid medical "
            "marijuana card, or if marijuana metabolites result from lawful "
            "Prop 207 use and the person is not actually impaired); "
            "(4) If the vehicle is a commercial motor vehicle that requires a "
            "CDL and the person has an alcohol concentration of 0.04 or more. "
            "Classification: First offense DUI is a class 1 misdemeanor. "
            "Penalties include minimum 10 consecutive days in jail (9 may be "
            "suspended if defendant completes alcohol screening), fines of at "
            "least $1,250, license suspension, ignition interlock device, and "
            "mandatory alcohol/drug screening and treatment. Second offense "
            "within 84 months: minimum 90 days jail, at least $3,000 in fines, "
            "license revocation for 1 year."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "MISDEMEANOR",
        "source": "ARS Title 28, Ch. 4",
    },
    {
        "code": "ARS 28-1382",
        "title": "Extreme DUI",
        "text": (
            "ARS 28-1382 (Driving or actual physical control while under the "
            "extreme influence of intoxicating liquor). (A) It is unlawful for a "
            "person to drive or be in actual physical control of a vehicle in "
            "this state if the person has an alcohol concentration as follows "
            "within two hours of driving or being in actual physical control: "
            "(1) 0.15 or more but less than 0.20 — 'extreme DUI'; "
            "(2) 0.20 or more — 'super extreme DUI.' "
            "Classification: Class 1 misdemeanor with enhanced penalties. "
            "First offense extreme DUI (0.15-0.199 BAC): minimum 30 consecutive "
            "days in jail (with the possibility of serving part on home detention "
            "after 2 days), minimum $2,500 in fines plus surcharges, ignition "
            "interlock device for 12 months, alcohol screening and treatment, "
            "community service. "
            "First offense super extreme DUI (0.20+ BAC): minimum 45 consecutive "
            "days in jail, minimum $3,250 in fines plus surcharges, ignition "
            "interlock device for 18 months. "
            "Second offense within 84 months for extreme DUI: minimum 120 days "
            "jail. Second offense super extreme: minimum 180 days jail. "
            "All mandatory jail time under this section is non-suspendable. "
            "The 84-month (7-year) lookback period applies for prior DUI "
            "convictions."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "MISDEMEANOR",
        "source": "ARS Title 28, Ch. 4",
    },
    {
        "code": "ARS 28-1383",
        "title": "Aggravated DUI",
        "text": (
            "ARS 28-1383 (Aggravated driving or actual physical control while "
            "under the influence). (A) A person is guilty of aggravated DUI if "
            "the person does any of the following: "
            "(1) Commits a DUI violation (28-1381 or 28-1382) while the person's "
            "driver license or privilege to drive is suspended, canceled, revoked, "
            "or refused, or while a restriction is placed on the person's driver "
            "license as a result of a prior DUI-related incident; "
            "(2) Commits a third or subsequent DUI violation within a period of "
            "84 months (7 years); "
            "(3) Commits a DUI violation while a person under fifteen years of "
            "age is in the vehicle; "
            "(4) Commits a DUI while required to have an ignition interlock device "
            "on the vehicle; "
            "(5) Commits a DUI while driving the wrong way on a highway. "
            "Classification: Aggravated DUI is a class 4 felony (class 6 felony "
            "for subsection (A)(3) — child in vehicle). "
            "Penalties: Mandatory prison — minimum 4 months in prison (DOC) for "
            "class 4 felony DUI; license revocation for at least 3 years; "
            "mandatory ignition interlock device; alcohol/drug screening and "
            "treatment; community restitution. "
            "Third DUI in 84 months: minimum 8 months prison. "
            "Wrong-way DUI: class 4 felony with enhanced penalties. "
            "Note: Aggravated DUI is the only DUI offense that is a felony "
            "rather than a misdemeanor."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 28, Ch. 4",
    },

    # ========================================================================
    # TITLE 13, CHAPTER 8 — WEAPONS OFFENSES (Title 13, Chapter 31)
    # ========================================================================
    {
        "code": "ARS 13-3101",
        "title": "Weapons Definitions",
        "text": (
            "ARS 13-3101 (Definitions — Weapons and explosives). Key definitions: "
            "'Deadly weapon' means anything designed for lethal use, including a "
            "firearm. "
            "'Firearm' means any loaded or unloaded handgun, pistol, revolver, "
            "rifle, shotgun, or other weapon that will or is designed to or may "
            "readily be converted to expel a projectile by the action of expanding "
            "gases, except that it does not include a firearm in permanently "
            "inoperable condition. "
            "'Prohibited possessor' means any person: (a) who has been found to "
            "constitute a danger to self or others or persistently or acutely "
            "disabled or gravely disabled pursuant to court order under ARS 36-540, "
            "and whose right to possess firearms has not been restored; (b) who has "
            "been convicted of a felony within or without this state, or who has "
            "been adjudicated delinquent and whose civil right to possess or carry "
            "a gun has not been restored; (c) who is at the time of possession "
            "serving a term of imprisonment in any correctional or detention facility; "
            "(d) who is at the time of possession serving a term of probation "
            "pursuant to a conviction for a domestic violence offense or a felony "
            "offense; (e) who is an undocumented alien or nonimmigrant alien "
            "traveling with or without documentation in this state; (f) who has "
            "been found incompetent pursuant to rule 11, Arizona Rules of Criminal "
            "Procedure, and whose right to possess a firearm has not been restored. "
            "'Prohibited weapon' includes bombs, grenades, rockets, mines, "
            "sawed-off shotguns (barrel less than 18 inches), sawed-off rifles "
            "(barrel less than 16 inches), and fully automatic firearms (unless "
            "federally registered). Note: Under Arizona law, silencers/suppressors "
            "are legal if in compliance with federal NFA requirements."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 31",
    },
    {
        "code": "ARS 13-3102",
        "title": "Misconduct Involving Weapons",
        "text": (
            "ARS 13-3102 (Misconduct involving weapons; defenses; classification; "
            "definitions). (A) A person commits misconduct involving weapons by "
            "knowingly: "
            "(1) Carrying a deadly weapon (except a pocket knife) concealed on "
            "his person or within his immediate control in or on a means of "
            "transportation — NOTE: as of 2010 (SB 1108), Arizona allows "
            "permitless concealed carry for persons 21+ who are not prohibited "
            "possessors, so this subsection has limited application; "
            "(4) Possessing a deadly weapon or prohibited weapon if the person "
            "is a prohibited possessor; "
            "(5) Selling or transferring a deadly weapon to a prohibited possessor; "
            "(6) Defacing a deadly weapon (removing serial number); "
            "(7) Possessing a defaced deadly weapon knowing it has been defaced; "
            "(8) Using or possessing a deadly weapon during the commission of "
            "any felony offense included in chapter 34 (drug offenses); "
            "(9) Discharging a firearm at an occupied structure in order to "
            "assist, promote, or further the interests of a criminal street gang; "
            "(12) Possessing a deadly weapon on school grounds (K-12); "
            "(13) Possessing a deadly weapon on the grounds of a nuclear or "
            "hydroelectric generating station; "
            "(14) Supplying, selling, or giving possession of a firearm to "
            "another person if the person knows or has reason to know that the "
            "other person would use the firearm in the commission of a felony; "
            "(15) Carrying a deadly weapon (other than a pocket knife with a "
            "blade 4 inches or less) into a polling place on election day; "
            "(16) Using, possessing, or exercising control over a deadly weapon "
            "in furtherance of any act of terrorism or in furtherance of a "
            "criminal street gang. "
            "Classification: Varies by subsection. Prohibited possessor with "
            "firearm is a class 4 felony. Possessing a prohibited weapon is "
            "a class 4 felony. Weapon on school grounds is a class 1 misdemeanor "
            "(class 6 felony if previously convicted). Drug offense with weapon "
            "is a class 4 felony."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 31",
    },

    # ========================================================================
    # TITLE 13, CHAPTER 9 — DOMESTIC VIOLENCE (Title 13, Chapter 36)
    # ========================================================================
    {
        "code": "ARS 13-3601",
        "title": "Domestic Violence — Designation and Definition",
        "text": (
            "ARS 13-3601 (Domestic violence; definition; classification; "
            "sentencing; conditions of probation). (A) 'Domestic violence' means "
            "any act that is a dangerous crime against children as defined in "
            "section 13-705 or an offense prescribed in sections 13-1102 through "
            "13-1204 (homicide and assault), 13-1302 through 13-1304 (kidnapping), "
            "13-1502 through 13-1504 (trespass), 13-1602 (criminal damage), "
            "13-1603 (criminal littering/polluting), 13-1604 (aggravated criminal "
            "damage), 13-2810 (interfering with judicial proceedings), 13-2904 "
            "(disorderly conduct), 13-2910 (cruelty to animals), 13-2915 "
            "(harassment by electronic communication), 13-2916 (use of telephone "
            "to terrify/intimidate/threaten/harass), 13-2921 (harassment), "
            "13-2921.01 (aggravated harassment), 13-2923 (stalking), 13-3019 "
            "(surreptitious photographing), 13-3601.02 (aggravated domestic "
            "violence), or 13-3623 (child or vulnerable adult abuse), if the "
            "relationship between the victim and the defendant is one of the "
            "following: "
            "(1) Spouse or former spouse; (2) Persons residing or having resided "
            "in the same household; (3) Parent and child; (4) Persons related by "
            "blood or court order as a parent/grandparent of a child in common; "
            "(5) The victim is pregnant by the defendant; (6) Persons who are or "
            "were in a romantic or sexual relationship. "
            "Enhancement: A domestic violence designation does not create a "
            "separate crime but attaches enhanced consequences to the underlying "
            "offense. Third domestic violence conviction within 84 months is "
            "aggravated domestic violence (ARS 13-3601.02), a class 5 felony. "
            "Conditions of probation typically include: domestic violence offender "
            "treatment program, no contact order, firearms prohibition if felony."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 36",
    },
    {
        "code": "ARS 13-3602",
        "title": "Order of Protection",
        "text": (
            "ARS 13-3602 (Order of protection). (A) A person may file a verified "
            "petition for an order of protection for the purpose of restraining a "
            "person from committing an act of domestic violence. (B) The petition "
            "shall be filed in the jurisdiction where the plaintiff or defendant "
            "resides, or where the acts of domestic violence occurred. "
            "(C) If the court finds reasonable cause to believe the defendant may "
            "commit an act of domestic violence or has committed an act of domestic "
            "violence, the court shall issue an order of protection. "
            "(D) The order of protection may include: "
            "(1) Enjoining the defendant from committing further acts of domestic "
            "violence; (2) Granting one party exclusive use and possession of the "
            "shared residence; (3) Restraining the defendant from contacting the "
            "plaintiff; (4) Granting temporary custody of minor children; "
            "(5) Enjoining the defendant from possessing or purchasing firearms "
            "for the duration of the order; (6) Other relief necessary to protect "
            "the victim. "
            "(E) An order of protection is effective for one year from the date of "
            "service. "
            "(F) A person who is restrained or enjoined by an order of protection "
            "and who violates the order is subject to arrest and prosecution under "
            "ARS 13-2810 (interfering with judicial proceedings). "
            "(G) Service shall be in a manner consistent with the rules of civil "
            "procedure. An order of protection may be served by a peace officer or "
            "by any other method authorized by the court. "
            "Note: An order of protection is a civil remedy but its violation is a "
            "criminal offense. Filing a false petition is a class 1 misdemeanor."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 36",
    },

    # ========================================================================
    # CRIMINAL PROCEDURE — ARREST, SEARCH, SEIZURE
    # ========================================================================
    {
        "code": "ARS 13-3883",
        "title": "Arrest Procedures — Arrest by Officer Without Warrant",
        "text": (
            "ARS 13-3883 (Arrest by officer without warrant). A peace officer, "
            "without a warrant, may arrest a person if the officer has probable "
            "cause to believe: "
            "(1) A felony has been committed and the person to be arrested has "
            "committed the felony; "
            "(2) A misdemeanor has been committed in the officer's presence and "
            "the person to be arrested has committed the offense; "
            "(3) The person to be arrested has committed any offense that the "
            "officer has probable cause to believe the person has committed and "
            "the officer has probable cause to believe that the person will not "
            "be apprehended unless immediately arrested, will cause injury to "
            "self or others, or will cause damage to property unless immediately "
            "arrested; "
            "(4) The person to be arrested has committed any public offense that "
            "makes the person removable from the United States; "
            "(5) The officer has received positive information by written, "
            "telegraphic, teletypic, telephonic, or radio communication from a "
            "law enforcement agency that holds a warrant for the person's arrest; "
            "(6) The officer has probable cause to believe that an order of "
            "protection has been served and the person has violated a provision "
            "of the order. "
            "Key principle: Warrantless arrest for a felony requires probable "
            "cause but not the officer's personal observation. Warrantless arrest "
            "for a misdemeanor generally requires the offense to be committed in "
            "the officer's presence (with exceptions for DV and certain other "
            "offenses)."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "ARS Title 13, Ch. 38",
    },
    {
        "code": "ARS 13-3884",
        "title": "Miranda Rights — Right to Counsel During Interrogation",
        "text": (
            "ARS 13-3884 (Interrogation — rights of person in custody). This "
            "section codifies Arizona's version of Miranda protections (consistent "
            "with Miranda v. Arizona, 384 U.S. 436 (1966), which originated in "
            "Arizona). Before any custodial interrogation, a peace officer shall "
            "inform the person of the following rights: "
            "(1) The person has the right to remain silent; "
            "(2) Anything the person says can and will be used against the person "
            "in a court of law; "
            "(3) The person has the right to the presence of an attorney during "
            "interrogation; "
            "(4) If the person cannot afford an attorney, one will be appointed "
            "before any questioning if the person so desires. "
            "If the person indicates in any manner that he or she wishes to remain "
            "silent or to have an attorney, the interrogation must cease. Any "
            "statement obtained in violation of these rights is inadmissible in "
            "the prosecution's case-in-chief. "
            "Critical note: Miranda v. Arizona was an Arizona case — the state's "
            "statutory and constitutional protections are deeply intertwined with "
            "federal Miranda doctrine. Arizona courts apply Miranda strictly, and "
            "the Arizona Constitution (Art. 2, Sec. 10) provides independent "
            "self-incrimination protections."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "ARS Title 13, Ch. 38",
    },
    {
        "code": "ARS 13-3887",
        "title": "Search and Seizure — Scope of Authority",
        "text": (
            "ARS 13-3887 and related provisions govern search and seizure authority "
            "in Arizona. Arizona's search and seizure framework mirrors the Fourth "
            "Amendment and Arizona Constitution Art. 2, Sec. 8. Key principles: "
            "(1) A search warrant is generally required to search a person, place, "
            "or thing, unless an exception applies. "
            "(2) Recognized exceptions to the warrant requirement include: consent, "
            "search incident to a lawful arrest, plain view, exigent circumstances, "
            "automobile exception (probable cause to believe vehicle contains "
            "contraband or evidence), inventory search, Terry stop and frisk "
            "(reasonable suspicion of criminal activity plus reasonable belief the "
            "person is armed and dangerous), hot pursuit, and community caretaking. "
            "(3) Evidence obtained in violation of Fourth Amendment or Arizona "
            "Constitution Art. 2, Sec. 8 is subject to the exclusionary rule — "
            "inadmissible at trial along with any derivative 'fruit of the "
            "poisonous tree.' "
            "(4) Arizona courts have held that the state constitution provides at "
            "least as much protection as the federal Fourth Amendment, and in some "
            "cases may provide greater protection (see State v. Bolt, State v. "
            "Ault). "
            "(5) Burden of proof: The prosecution bears the burden of establishing "
            "the legality of a warrantless search."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "ARS Title 13, Ch. 38",
    },
    {
        "code": "ARS 13-3903",
        "title": "Search Warrants — Issuance and Requirements",
        "text": (
            "ARS 13-3903 and related provisions (ARS 13-3911 through 13-3921) "
            "govern the issuance and execution of search warrants. "
            "(A) A search warrant may be issued by a magistrate upon a sworn "
            "affidavit establishing probable cause to believe that contraband, "
            "fruits of a crime, instrumentalities of a crime, or other evidence "
            "relevant to the commission of a crime is located at the place to "
            "be searched. "
            "(B) The warrant shall describe with particularity: (1) the person, "
            "place, or thing to be searched, and (2) the items to be seized. "
            "(C) The warrant must be executed within five days of issuance. "
            "(D) The officer executing the warrant shall give a copy of the "
            "warrant and a receipt for property seized to the person from whom "
            "the property is taken, or shall leave them at the place of the "
            "search. "
            "(E) A return and inventory must be made promptly to the issuing "
            "magistrate. "
            "(F) Search warrants may be issued for electronic data and "
            "communications stored by third-party service providers, subject to "
            "federal Stored Communications Act requirements. "
            "Telephonic warrants: Arizona permits telephonic search warrants "
            "under ARS 13-3914 — a warrant may be issued based on sworn oral "
            "testimony communicated by telephone or other reliable electronic "
            "means when circumstances make it reasonable to dispense with a "
            "written affidavit. "
            "Knock-and-announce: Officers must generally announce their presence "
            "and purpose before executing a search warrant unless exigent "
            "circumstances exist (risk of destruction of evidence, danger to "
            "officers)."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "ARS Title 13, Ch. 39",
    },
    {
        "code": "ARS 13-3925",
        "title": "Electronic Surveillance — Wiretapping and Eavesdropping",
        "text": (
            "ARS 13-3005 through 13-3017 (intercepting communications; "
            "eavesdropping) govern electronic surveillance in Arizona. Key provisions: "
            "(1) Arizona is a one-party consent state — a person may lawfully "
            "record or intercept a conversation if at least one party to the "
            "communication consents (ARS 13-3005). "
            "(2) It is unlawful to intercept any wire, electronic, or oral "
            "communication without the consent of at least one party, except "
            "as authorized by court order (ARS 13-3005(A)). "
            "(3) Law enforcement may obtain a court order authorizing interception "
            "of communications upon a showing of probable cause that the "
            "interception will reveal evidence of specifically enumerated serious "
            "felonies (ARS 13-3010). "
            "(4) Violation of the wiretapping statute is a class 5 felony "
            "(ARS 13-3005). "
            "(5) Evidence obtained through unlawful interception is inadmissible "
            "in any court proceeding (ARS 13-3012). "
            "(6) A person whose communications have been unlawfully intercepted "
            "has a civil cause of action for damages (ARS 13-3016). "
            "Note: Arizona's one-party consent rule means that a participant in a "
            "conversation (or someone with the consent of a participant) may "
            "record the conversation without notifying the other parties. This "
            "applies to both in-person and telephone communications."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "ARS Title 13, Ch. 30",
    },

    # ========================================================================
    # ARIZONA CONSTITUTION — CRIMINAL RIGHTS
    # ========================================================================
    {
        "code": "AZ CONST ART 2 SEC 4",
        "title": "Due Process of Law",
        "text": (
            "Arizona Constitution, Article 2, Section 4 (Due process of law). "
            "'No person shall be deprived of life, liberty, or property without "
            "due process of law.' This provision mirrors the Fourteenth Amendment "
            "to the U.S. Constitution and guarantees both substantive and procedural "
            "due process under Arizona law. Arizona courts apply due process "
            "independently under the state constitution and may afford greater "
            "protections than federal due process analysis. Due process in Arizona "
            "criminal proceedings requires: (1) adequate notice of the charges, "
            "(2) opportunity to be heard and present a defense, (3) an impartial "
            "tribunal, (4) the right to confront and cross-examine witnesses, "
            "(5) the right to counsel, (6) proof beyond a reasonable doubt for "
            "every element of the charged offense, (7) the right to appeal. "
            "Due process also prohibits the state from using fundamentally unfair "
            "procedures, suppressing material exculpatory evidence (Brady v. "
            "Maryland), or pursuing vindictive prosecution."
        ),
        "category": "constitutional",
        "jurisdiction": "AZ",
        "severity": "CONSTITUTIONAL",
        "source": "Arizona Constitution, Article 2",
    },
    {
        "code": "AZ CONST ART 2 SEC 8",
        "title": "Right to Be Free from Unreasonable Search and Seizure",
        "text": (
            "Arizona Constitution, Article 2, Section 8 (Right of privacy; search "
            "and seizure). 'No person shall be disturbed in his private affairs, "
            "or his home invaded, without authority of law.' This provision is "
            "Arizona's analogue to the Fourth Amendment and has been interpreted "
            "by Arizona courts to provide protections that are at least co-extensive "
            "with — and sometimes broader than — federal Fourth Amendment protections. "
            "Key applications: (1) Warrantless searches are presumptively "
            "unreasonable; the state bears the burden of proving a valid exception. "
            "(2) The exclusionary rule applies — evidence obtained in violation of "
            "this section is inadmissible. (3) Arizona courts have recognized a "
            "reasonable expectation of privacy in sealed mail, bank records, and "
            "certain electronic data. (4) The 'private affairs' language has been "
            "interpreted more broadly than the federal 'persons, houses, papers, "
            "and effects' language, potentially extending privacy protections to "
            "contexts not covered by the Fourth Amendment. "
            "Notable: The Arizona Supreme Court in State v. Jean (1991) held that "
            "Article 2, Section 8 provides an independent basis for suppression "
            "that is not dependent on federal Fourth Amendment analysis."
        ),
        "category": "constitutional",
        "jurisdiction": "AZ",
        "severity": "CONSTITUTIONAL",
        "source": "Arizona Constitution, Article 2",
    },
    {
        "code": "AZ CONST ART 2 SEC 10",
        "title": "Self-Incrimination — Right Against",
        "text": (
            "Arizona Constitution, Article 2, Section 10 (Self-incrimination; double "
            "jeopardy). 'No person shall be compelled in any criminal case to give "
            "evidence against himself, or be twice put in jeopardy for the same "
            "offense.' This provision provides two independent protections: "
            "(1) Privilege against self-incrimination: Mirrors the Fifth Amendment "
            "and was the basis for the landmark Miranda v. Arizona (1966) decision. "
            "A person has the right to refuse to answer questions that may "
            "incriminate them in criminal proceedings, grand jury proceedings, "
            "and any other governmental proceeding. The privilege must be "
            "affirmatively invoked (except during custodial interrogation, where "
            "Miranda warnings are required). The prosecution may not comment on "
            "the defendant's exercise of the right to remain silent at trial "
            "(Griffin v. California; State v. Sorrell). "
            "(2) Double jeopardy: Prohibits a second prosecution for the same "
            "offense after acquittal, a second prosecution after conviction, "
            "and multiple punishments for the same offense. Arizona applies the "
            "'same elements' test (Blockburger) to determine whether two offenses "
            "are the 'same offense' for double jeopardy purposes. Jeopardy "
            "attaches in a jury trial when the jury is empaneled and sworn, and "
            "in a bench trial when the first witness is sworn."
        ),
        "category": "constitutional",
        "jurisdiction": "AZ",
        "severity": "CONSTITUTIONAL",
        "source": "Arizona Constitution, Article 2",
    },
    {
        "code": "AZ CONST ART 2 SEC 15",
        "title": "Confrontation of Witnesses",
        "text": (
            "Arizona Constitution, Article 2, Section 15 (Confrontation of "
            "witnesses). 'In criminal prosecutions, the accused shall have the "
            "right to... be confronted with the witnesses against him...' This "
            "right is the state constitutional analogue to the Sixth Amendment "
            "Confrontation Clause. Key applications in Arizona: "
            "(1) The defendant has the right to face-to-face confrontation with "
            "witnesses who testify against them at trial; "
            "(2) The defendant has the right to cross-examine all prosecution "
            "witnesses; "
            "(3) Under Crawford v. Washington (2004), testimonial out-of-court "
            "statements are admissible only if the declarant is unavailable AND "
            "the defendant had a prior opportunity to cross-examine the declarant; "
            "(4) Arizona courts apply Crawford strictly — forensic lab reports, "
            "911 calls (depending on primary purpose), and prior testimony are "
            "all subject to Confrontation Clause analysis; "
            "(5) Limited exceptions exist for child witnesses (closed-circuit "
            "testimony under ARS 13-4253 upon a finding that the child is unable "
            "to testify in the defendant's presence); "
            "(6) A defendant may forfeit the right to confrontation through "
            "wrongdoing that procures the witness's unavailability (forfeiture "
            "by wrongdoing doctrine). "
            "Arizona courts treat this right as fundamental and its violation "
            "as structural error requiring reversal."
        ),
        "category": "constitutional",
        "jurisdiction": "AZ",
        "severity": "CONSTITUTIONAL",
        "source": "Arizona Constitution, Article 2",
    },
    {
        "code": "AZ CONST ART 2 SEC 24",
        "title": "Right to Bear Arms",
        "text": (
            "Arizona Constitution, Article 2, Section 24 (Right to bear arms). "
            "'The right of the individual citizen to bear arms in defense of "
            "himself or the state shall not be impaired, but nothing in this "
            "section shall be construed as authorizing individuals or corporations "
            "to organize, maintain, or employ an armed body of men.' "
            "Key aspects: (1) Arizona's right to bear arms is an individual right, "
            "not conditioned on militia service — this was explicit in Arizona's "
            "constitution decades before the U.S. Supreme Court's Heller decision "
            "(2008); "
            "(2) The phrase 'shall not be impaired' has been interpreted as "
            "providing strong protection against firearms regulations; "
            "(3) Arizona is a 'constitutional carry' state — no permit is required "
            "for open or concealed carry of a firearm by persons 21 and older who "
            "are not prohibited possessors (ARS 13-3101, 13-3102); "
            "(4) Prohibited possessors (felons, persons subject to certain mental "
            "health adjudications) may still be lawfully restricted from possessing "
            "firearms; "
            "(5) The right extends to 'arms' broadly — not limited to firearms; "
            "(6) Arizona has state preemption of local firearms regulations "
            "(ARS 13-3108) — cities and counties may not enact firearm laws more "
            "restrictive than state law."
        ),
        "category": "constitutional",
        "jurisdiction": "AZ",
        "severity": "CONSTITUTIONAL",
        "source": "Arizona Constitution, Article 2",
    },

    # ========================================================================
    # SENTENCING — TITLE 13, CHAPTER 7
    # ========================================================================
    {
        "code": "ARS 13-701",
        "title": "Sentence of Imprisonment — General Provisions",
        "text": (
            "ARS 13-701 (Sentence of imprisonment for felony). Sets forth the "
            "general framework for felony sentencing in Arizona. Key provisions: "
            "(1) A sentence of imprisonment for a felony shall be a definite "
            "term of years as set forth in section 13-702 (non-dangerous) or "
            "section 13-704 (dangerous). "
            "(2) The court shall consider aggravating and mitigating circumstances "
            "in determining the appropriate sentence within the statutory range. "
            "(3) Aggravating circumstances must be found by the jury beyond a "
            "reasonable doubt (except prior convictions, which are found by the "
            "court) pursuant to Blakely v. Washington / Apprendi v. New Jersey. "
            "(4) Mitigating circumstances need only be proven by a preponderance "
            "of the evidence. "
            "(5) Statutory aggravating factors include: infliction of serious "
            "physical injury, use of a deadly weapon, presence of an accomplice, "
            "commission for pecuniary gain, especially heinous/cruel/depraved "
            "manner, victim's age (very young or elderly), violation of position "
            "of trust, prior felony convictions. "
            "(6) Statutory mitigating factors include: the defendant's age, "
            "duress, minor participation, mental capacity, good character, "
            "cooperation with law enforcement, remorse, and any other factor "
            "relevant to a just sentence. "
            "Truth-in-sentencing: Arizona abolished parole in 1993. Defendants "
            "sentenced to prison must serve at least 85% of their sentence before "
            "being eligible for release (100% for dangerous crimes against children "
            "and certain sex offenses)."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 7",
    },
    {
        "code": "ARS 13-702",
        "title": "Sentencing Ranges for Non-Dangerous Felonies",
        "text": (
            "ARS 13-702 (First time felony offenders; sentencing). Establishes "
            "the sentencing ranges for non-dangerous, non-repetitive felony "
            "offenses. Ranges (in years of imprisonment): "
            "Class 2 felony: Mitigated 3, Minimum 4, Presumptive 5, Maximum 10, "
            "Aggravated 12.5. "
            "Class 3 felony: Mitigated 2, Minimum 2.5, Presumptive 3.5, Maximum 7, "
            "Aggravated 8.75. "
            "Class 4 felony: Mitigated 1, Minimum 1.5, Presumptive 2.5, Maximum 3, "
            "Aggravated 3.75. "
            "Class 5 felony: Mitigated 0.5 (6 months), Minimum 0.75, Presumptive "
            "1.5, Maximum 2, Aggravated 2.5. "
            "Class 6 felony: Mitigated 0.33 (4 months), Minimum 0.5, Presumptive "
            "1, Maximum 1.5, Aggravated 2. "
            "Notes: (1) The presumptive sentence is the starting point; the court "
            "departs upward for aggravating factors or downward for mitigating "
            "factors. (2) Class 6 felonies are 'wobblers' — the court may designate "
            "a class 6 felony as a class 1 misdemeanor at sentencing or after "
            "successful completion of probation. (3) Probation-eligible: All "
            "non-dangerous first-time felony offenders are eligible for probation "
            "(suspension of sentence) at the court's discretion, except for "
            "certain enumerated offenses. (4) These ranges apply only to first "
            "offenders — see ARS 13-703 (dangerous offenses) and 13-704 "
            "(repetitive offenders) for enhanced ranges."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 7",
    },
    {
        "code": "ARS 13-703",
        "title": "Dangerous Offenses — Sentencing Enhancements",
        "text": (
            "ARS 13-703 (Dangerous offenses; sentencing). Establishes enhanced, "
            "mandatory prison sentences for 'dangerous offenses' — offenses "
            "involving the discharge, use, or threatening exhibition of a deadly "
            "weapon or dangerous instrument, or the intentional or knowing "
            "infliction of serious physical injury. "
            "Dangerous offense sentencing ranges (FIRST offense, in years): "
            "Class 2 felony: Mitigated 7, Minimum 7, Presumptive 10.5, Maximum 21, "
            "Aggravated 21. "
            "Class 3 felony: Mitigated 5, Minimum 5, Presumptive 7.5, Maximum 15, "
            "Aggravated 15. "
            "Class 4 felony: Mitigated 4, Minimum 4, Presumptive 6, Maximum 8, "
            "Aggravated 8. "
            "Class 5 felony: Mitigated 2, Minimum 2, Presumptive 3, Maximum 4, "
            "Aggravated 4. "
            "Class 6 felony: Mitigated 1.5, Minimum 1.5, Presumptive 2.25, "
            "Maximum 3, Aggravated 3. "
            "Critical points: (1) Dangerous offenses carry MANDATORY prison — no "
            "probation is available. (2) The 'dangerous' designation is a finding "
            "of fact that must be alleged in the charging document and found by "
            "the jury beyond a reasonable doubt. (3) Dangerous offense ranges "
            "roughly double the non-dangerous ranges. (4) Repeat dangerous "
            "offenders face dramatically increased ranges — second dangerous "
            "offense ranges approximately double again, and third dangerous "
            "offense ranges can reach natural life."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 7",
    },
    {
        "code": "ARS 13-704",
        "title": "Repetitive Offenders — Sentencing Enhancements",
        "text": (
            "ARS 13-704 (Repetitive offenders; sentencing). Provides enhanced "
            "sentencing ranges for defendants with prior felony convictions. "
            "Category 1 repetitive offender (one historical prior felony conviction): "
            "Class 2: Min 4, Presumptive 5, Max 10 (non-dangerous). "
            "Class 3: Min 2.5, Presumptive 3.5, Max 7. "
            "Class 4: Min 1.5, Presumptive 2.5, Max 3. "
            "Class 5: Min 0.75, Presumptive 1.5, Max 2. "
            "Class 6: Min 0.5, Presumptive 1, Max 1.5. "
            "Category 2 repetitive offender (two historical prior felony "
            "convictions): Enhanced ranges with higher minimum and maximum terms. "
            "Category 3 repetitive offender (three or more historical prior "
            "felony convictions): The most severe non-dangerous ranges, with "
            "significantly elevated minimums and maximums. "
            "Key rules: (1) 'Historical prior felony conviction' is defined in "
            "ARS 13-105 and includes prior convictions from Arizona or any other "
            "jurisdiction for conduct that would constitute a felony under Arizona "
            "law. (2) Prior convictions are found by the court (judge), not the "
            "jury. (3) The 'category' of repetitive offender determines which "
            "sentencing range applies. (4) Repetitive offender status can stack "
            "with dangerous offense designation for dramatically increased "
            "ranges. (5) Certain prior convictions 'wash out' if a sufficient "
            "period has elapsed without new convictions."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "REFERENCE",
        "source": "ARS Title 13, Ch. 7",
    },
    {
        "code": "ARS 13-705",
        "title": "Dangerous Crimes Against Children — Sentencing",
        "text": (
            "ARS 13-705 (Dangerous crimes against children; sentences; "
            "definitions). Provides the most severe sentencing enhancements in "
            "Arizona criminal law for offenses committed against children under "
            "fifteen years of age. "
            "(A) 'Dangerous crime against children' means any of the following "
            "committed against a minor under 15: second degree murder, aggravated "
            "assault (serious physical injury or deadly weapon), sexual assault, "
            "molestation of a child, sexual conduct with a minor, commercial sexual "
            "exploitation of a minor, sexual exploitation of a minor, child abuse "
            "(ARS 13-3623), kidnapping, and sexual abuse. "
            "(B) Sentencing ranges for DCAC (first offense, in years): "
            "Class 2 felony: Minimum 10, Presumptive 17, Maximum 24. "
            "Class 3 felony: Minimum 5, Presumptive 10, Maximum 15. "
            "Class 4 felony: Minimum 2, Presumptive 5, Maximum 8 (varies). "
            "Class 6 felony: Minimum 1, Presumptive 2.5, Maximum 4 (varies). "
            "(C) Critical provisions: (1) NO probation — mandatory prison. "
            "(2) Sentences must be served at 100% (no early release credits — "
            "day-for-day). (3) DCAC sentences must be served CONSECUTIVELY, not "
            "concurrently, if there are multiple victims or multiple counts. "
            "(4) Repeat DCAC offenders face dramatically enhanced sentences: a "
            "second DCAC offense for a class 2 felony carries a presumptive of "
            "28 years with a maximum of 35 years, and a third DCAC offense can "
            "carry a sentence of natural life. "
            "(5) Lifetime probation (sex offender registration) applies to all "
            "DCAC sex offenses."
        ),
        "category": "statute",
        "jurisdiction": "AZ",
        "severity": "FELONY",
        "source": "ARS Title 13, Ch. 7",
    },

    # ========================================================================
    # ARIZONA RULES OF EVIDENCE
    # ========================================================================
    {
        "code": "ARIZ R EVID 401",
        "title": "Test for Relevant Evidence",
        "text": (
            "Arizona Rule of Evidence 401 (Test for Relevant Evidence). Evidence "
            "is relevant if: (a) it has any tendency to make a fact more or less "
            "probable than it would be without the evidence; and (b) the fact is "
            "of consequence in determining the action. This is a very low threshold "
            "— evidence need only have 'any tendency' to affect the probability of "
            "a consequential fact. Relevance is determined by logic and experience, "
            "not by legal standards of sufficiency. Arizona's Rule 401 is identical "
            "to Federal Rule of Evidence 401. All evidence must pass this threshold "
            "test before any other rule of admissibility is applied."
        ),
        "category": "evidence-rule",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Evidence",
    },
    {
        "code": "ARIZ R EVID 402",
        "title": "General Admissibility of Relevant Evidence",
        "text": (
            "Arizona Rule of Evidence 402 (General Admissibility of Relevant "
            "Evidence). Relevant evidence is admissible unless any of the following "
            "provides otherwise: the United States Constitution, the Arizona "
            "Constitution, a statute, these rules, or other rules applicable in "
            "Arizona courts. Irrelevant evidence is not admissible. This rule "
            "establishes the default: all relevant evidence comes in unless there "
            "is a specific rule excluding it. This is the 'baseline admissibility' "
            "rule. The party seeking to exclude relevant evidence bears the burden "
            "of identifying a specific exclusionary rule that applies."
        ),
        "category": "evidence-rule",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Evidence",
    },
    {
        "code": "ARIZ R EVID 403",
        "title": "Excluding Relevant Evidence — Prejudice, Confusion, Waste of Time",
        "text": (
            "Arizona Rule of Evidence 403 (Excluding Relevant Evidence for "
            "Prejudice, Confusion, Waste of Time, or Other Reasons). The court may "
            "exclude relevant evidence if its probative value is substantially "
            "outweighed by a danger of one or more of the following: unfair "
            "prejudice, confusing the issues, misleading the jury, undue delay, "
            "wasting time, or needlessly presenting cumulative evidence. "
            "Key points: (1) The standard is 'substantially outweighed' — the "
            "rule favors admissibility; it is not a 50/50 balancing test. "
            "(2) 'Unfair prejudice' means an undue tendency to suggest a decision "
            "on an improper basis, commonly an emotional one such as sympathy, "
            "horror, or contempt. All evidence against a party is 'prejudicial' "
            "— only 'unfairly' prejudicial evidence is excludable. "
            "(3) Rule 403 is the primary tool for excluding gruesome photographs, "
            "inflammatory evidence, prior bad acts that are marginally relevant, "
            "and repetitive evidence. "
            "(4) The trial court has broad discretion under Rule 403; appellate "
            "review is for abuse of discretion. "
            "(5) A limiting instruction under Rule 105 may be an alternative to "
            "exclusion — the court may admit evidence for one purpose while "
            "instructing the jury not to consider it for another."
        ),
        "category": "evidence-rule",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Evidence",
    },
    {
        "code": "ARIZ R EVID 404",
        "title": "Character Evidence; Prior Bad Acts",
        "text": (
            "Arizona Rule of Evidence 404 (Character Evidence; Crimes or Other "
            "Acts). (a) Character Evidence: (1) Evidence of a person's character "
            "or character trait is not admissible to prove that on a particular "
            "occasion the person acted in accordance with the character or trait. "
            "(2) Exceptions for a defendant in a criminal case: (A) a defendant "
            "may offer evidence of the defendant's pertinent trait, and if the "
            "evidence is admitted, the prosecutor may offer evidence to rebut it; "
            "(B) a defendant may offer evidence of an alleged victim's pertinent "
            "trait (subject to Rule 412 in sex offense cases), and if admitted, "
            "the prosecutor may rebut AND offer evidence of the defendant's same "
            "trait; (C) in a homicide case, the prosecutor may offer evidence of "
            "the alleged victim's trait of peacefulness to rebut evidence that "
            "the victim was the first aggressor. "
            "(b) Crimes, Wrongs, or Other Acts: (1) Evidence of a crime, wrong, "
            "or other act is not admissible to prove a person's character in "
            "order to show that on a particular occasion the person acted in "
            "accordance with the character. (2) This evidence MAY be admissible "
            "for another purpose, such as proving motive, opportunity, intent, "
            "preparation, plan, knowledge, identity, absence of mistake, or lack "
            "of accident. This list is commonly remembered by the mnemonic "
            "'MIMIC' (Motive, Intent, Mistake/absence of, Identity, Common plan "
            "or scheme). "
            "(3) On request by a defendant, the prosecutor must provide "
            "reasonable notice before trial of the general nature of any 404(b) "
            "evidence the prosecutor intends to offer."
        ),
        "category": "evidence-rule",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Evidence",
    },
    {
        "code": "ARIZ R EVID 702",
        "title": "Expert Witness Testimony",
        "text": (
            "Arizona Rule of Evidence 702 (Testimony by Expert Witnesses). A "
            "witness who is qualified as an expert by knowledge, skill, "
            "experience, training, or education may testify in the form of an "
            "opinion or otherwise if: (a) the expert's scientific, technical, "
            "or other specialized knowledge will help the trier of fact to "
            "understand the evidence or to determine a fact in issue; (b) the "
            "testimony is based on sufficient facts or data; (c) the testimony "
            "is the product of reliable principles and methods; and (d) the "
            "expert has reliably applied the principles and methods to the facts "
            "of the case. "
            "Arizona standard: Arizona adopted the Daubert standard effective "
            "January 1, 2012 (replacing the Frye 'general acceptance' test). "
            "Under Daubert/Rule 702, the trial court acts as a gatekeeper and "
            "must evaluate: (1) whether the expert's methodology is scientifically "
            "valid (can be and has been tested, subjected to peer review, known "
            "error rate, general acceptance in the relevant scientific community); "
            "(2) whether the methodology has been properly applied to the facts. "
            "Common expert testimony in Arizona criminal cases includes: forensic "
            "pathology (cause of death), ballistics, DNA analysis, toxicology "
            "(BAC/drug levels), digital forensics, accident reconstruction, "
            "fingerprint analysis, psychology (competency/insanity evaluations), "
            "and domestic violence dynamics."
        ),
        "category": "evidence-rule",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Evidence",
    },
    {
        "code": "ARIZ R EVID 801",
        "title": "Hearsay — Definitions",
        "text": (
            "Arizona Rule of Evidence 801 (Definitions That Apply to Hearsay). "
            "(a) 'Statement' means a person's oral assertion, written assertion, "
            "or nonverbal conduct if the person intended it as an assertion. "
            "(b) 'Declarant' means the person who made the statement. "
            "(c) 'Hearsay' means a statement that: (1) the declarant does not "
            "make while testifying at the current trial or hearing; and (2) a "
            "party offers in evidence to prove the truth of the matter asserted "
            "in the statement. "
            "(d) Statements that are NOT hearsay (exclusions): "
            "(d)(1) Opposing party's statement — a statement offered against an "
            "opposing party that was: (A) made by the party in an individual "
            "capacity; (B) adopted by the party; (C) made by an authorized "
            "spokesperson; (D) made by the party's agent or employee on a matter "
            "within the scope of the relationship while it existed; or (E) made "
            "by a co-conspirator during and in furtherance of the conspiracy. "
            "(d)(2) Prior statements by a witness — a declarant-witness's prior "
            "statement is not hearsay if: (A) inconsistent with the declarant's "
            "testimony and given under penalty of perjury; (B) consistent with "
            "the declarant's testimony and offered to rebut a charge of recent "
            "fabrication or improper influence/motive; or (C) identifies a person "
            "as someone the declarant perceived earlier. "
            "Key point: The definition of hearsay requires that the statement be "
            "offered 'to prove the truth of the matter asserted' — if offered for "
            "a non-hearsay purpose (e.g., to show notice, effect on the listener, "
            "verbal act, state of mind), it is not hearsay regardless of form."
        ),
        "category": "evidence-rule",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Evidence",
    },
    {
        "code": "ARIZ R EVID 802",
        "title": "Hearsay — General Exclusion",
        "text": (
            "Arizona Rule of Evidence 802 (The Rule Against Hearsay). Hearsay is "
            "not admissible unless any of the following provides otherwise: a "
            "federal statute, these rules, or other rules prescribed by the "
            "Arizona Supreme Court. This is the general rule of exclusion — "
            "hearsay statements are presumptively inadmissible. The exceptions "
            "are set forth in Rules 803 (exceptions regardless of declarant "
            "availability), 804 (exceptions when declarant is unavailable), and "
            "807 (residual exception). The rationale for excluding hearsay is "
            "that the opposing party had no opportunity to cross-examine the "
            "declarant regarding perception, memory, narration, and sincerity. "
            "Even if hearsay fits an exception, it must still satisfy the "
            "Confrontation Clause requirements under Crawford v. Washington "
            "(2004) if offered against a criminal defendant — testimonial hearsay "
            "is inadmissible unless the declarant is unavailable and the defendant "
            "had a prior opportunity to cross-examine."
        ),
        "category": "evidence-rule",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Evidence",
    },
    {
        "code": "ARIZ R EVID 803",
        "title": "Hearsay Exceptions — Declarant Availability Immaterial",
        "text": (
            "Arizona Rule of Evidence 803 (Exceptions to the Rule Against Hearsay — "
            "Regardless of Whether the Declarant Is Available as a Witness). The "
            "following are not excluded by the rule against hearsay, regardless of "
            "whether the declarant is available as a witness: "
            "(1) Present sense impression — statement describing or explaining an "
            "event or condition, made while or immediately after the declarant "
            "perceived it; "
            "(2) Excited utterance — statement relating to a startling event or "
            "condition, made while the declarant was under the stress of excitement "
            "that it caused; "
            "(3) Then-existing mental, emotional, or physical condition — statement "
            "of the declarant's then-existing state of mind (intent, plan, motive, "
            "design, mental feeling, pain, or bodily health); "
            "(4) Statement made for medical diagnosis or treatment — describing "
            "medical history, past or present symptoms, pain, sensations, or the "
            "inception or general character of the cause or external source thereof, "
            "to the extent reasonably pertinent to diagnosis or treatment; "
            "(5) Recorded recollection — a record on a matter the witness once knew "
            "about but now cannot recall well enough to testify fully and accurately, "
            "shown to have been made or adopted when the matter was fresh in the "
            "witness's memory and to reflect the witness's knowledge correctly; "
            "(6) Records of a regularly conducted activity (business records); "
            "(8) Public records — records setting out the office's activities, "
            "matters observed pursuant to a legal duty, or in civil cases and "
            "against the government in criminal cases, factual findings from a "
            "legally authorized investigation; "
            "(18) Statements in learned treatises — established as reliable "
            "authority by expert testimony or judicial notice. "
            "In Arizona criminal cases, the most commonly invoked Rule 803 "
            "exceptions are: excited utterance (especially 911 calls and "
            "spontaneous statements to police), business records (phone/financial "
            "records), public records, and statements for medical treatment "
            "(particularly in DV and child abuse cases)."
        ),
        "category": "evidence-rule",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Evidence",
    },

    # ========================================================================
    # ARIZONA RULES OF CRIMINAL PROCEDURE
    # ========================================================================
    {
        "code": "ARIZ R CRIM P 6",
        "title": "Right to Counsel",
        "text": (
            "Arizona Rule of Criminal Procedure 6 (Right to Counsel). "
            "(a) Right to Counsel at State Expense: A defendant charged with an "
            "offense for which a sentence of incarceration may be imposed is "
            "entitled to be represented by counsel at every stage of the "
            "proceedings. If the defendant is determined to be indigent, the court "
            "shall appoint counsel at public expense. "
            "(b) Scope of Right: The right attaches at the initial appearance and "
            "continues through appeal. The right applies at all critical stages, "
            "including arraignment, preliminary hearing, trial, sentencing, and "
            "first appeal of right. "
            "(c) Waiver: A defendant may waive the right to counsel, but only "
            "after the court conducts a thorough colloquy to determine that the "
            "waiver is knowing, intelligent, and voluntary. The court must advise "
            "the defendant of the nature of the charges, the possible penalties, "
            "the dangers of self-representation, and that the waiver can be "
            "withdrawn at any time. "
            "(d) Appointment of Advisory Counsel: Even when a defendant elects "
            "self-representation, the court may appoint advisory counsel (standby "
            "counsel) to assist the defendant. "
            "(e) Ineffective Assistance of Counsel: A defendant who received "
            "constitutionally deficient representation may raise a claim of "
            "ineffective assistance of counsel through a Rule 32/33 "
            "post-conviction relief petition. The standard is Strickland v. "
            "Washington — deficient performance AND resulting prejudice."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Criminal Procedure",
    },
    {
        "code": "ARIZ R CRIM P 7",
        "title": "Release Conditions — Bail",
        "text": (
            "Arizona Rule of Criminal Procedure 7 (Release — formerly Rule 7 / "
            "Rule 8). Note: Arizona reorganized its Rules of Criminal Procedure "
            "effective January 1, 2018. Release provisions are now primarily "
            "under Rule 7. Key provisions: "
            "(a) Presumption of Release: A person charged with a bailable offense "
            "is entitled to release on the least restrictive conditions that will "
            "reasonably assure the person's appearance and protect the community. "
            "(b) Types of Release: (1) Release on recognizance (OR); (2) Release "
            "on unsecured appearance bond; (3) Release into the custody of a "
            "designated person or organization; (4) Release on conditions (curfew, "
            "no contact, GPS monitoring, etc.); (5) Release on a secured appearance "
            "bond (monetary bail). "
            "(c) Factors for Release Decision: Nature and circumstances of the "
            "offense, weight of evidence, defendant's criminal history, ties to "
            "the community, employment, financial resources, character, mental "
            "condition, length of residence, prior failures to appear. "
            "(d) Non-Bailable Offenses: Under Arizona Constitution Art. 2, Sec. 22 "
            "(amended by Proposition 103, 2002), bail may be denied for: "
            "(1) Capital offenses when proof is evident or presumption great; "
            "(2) Sexual assault; (3) Sexual conduct with a minor under 15; "
            "(4) Other felony offenses if the person charged poses a substantial "
            "danger and no conditions of release will reasonably assure community "
            "safety. "
            "(e) The court must hold a hearing on a motion to deny bail within "
            "24 hours of the initial appearance (or as soon as practicable)."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Criminal Procedure",
    },
    {
        "code": "ARIZ R CRIM P 15",
        "title": "Disclosure — Discovery in Criminal Cases",
        "text": (
            "Arizona Rule of Criminal Procedure 15 (Disclosure). Arizona uses an "
            "'open file' disclosure system rather than the federal model. Key "
            "provisions: "
            "(a) Prosecutor's Disclosure Obligations: The state must disclose to "
            "the defense all of the following that is in its possession or control "
            "or that is available through the exercise of due diligence: "
            "(1) Names and addresses of all witnesses the state intends to call, "
            "together with their relevant written or recorded statements; "
            "(2) All statements of the defendant and any co-defendants; "
            "(3) The defendant's prior criminal record; "
            "(4) All documents, photographs, recordings, and tangible objects the "
            "state intends to use at trial or that are material to the defense; "
            "(5) All results of physical or mental examinations, scientific tests, "
            "experiments, or comparisons (lab reports, forensic results); "
            "(6) A list of all expert witnesses and their opinions and the bases "
            "and reasons therefor; "
            "(7) All material or information that tends to mitigate or negate the "
            "defendant's guilt (Brady material) — this obligation is constitutional "
            "and continuing. "
            "(b) Defense Disclosure Obligations: The defense must disclose "
            "witnesses it intends to call, expert witness reports, and notice of "
            "defenses (alibi, insanity, self-defense). "
            "(c) Continuing Duty: Both parties have a continuing obligation to "
            "disclose as new information becomes available. "
            "(d) Sanctions for Non-Disclosure: The court may order immediate "
            "disclosure, grant a continuance, preclude the undisclosed evidence, "
            "or dismiss the case. "
            "Critical note: Arizona's disclosure rules are broader than federal "
            "discovery — Arizona requires open-file disclosure of virtually "
            "all prosecution evidence, not just Brady material."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Criminal Procedure",
    },
    {
        "code": "ARIZ R CRIM P 15.1",
        "title": "Depositions in Criminal Cases",
        "text": (
            "Arizona Rule of Criminal Procedure 15.1 (Depositions — formerly "
            "Rule 16). Arizona is one of the few states that allows depositions "
            "in criminal cases as a matter of right. Key provisions: "
            "(a) Right to Depose: The state and the defense each have the right "
            "to take oral depositions of any person who has been disclosed as a "
            "witness (or whose identity has been otherwise ascertained). "
            "(b) Notice: Reasonable written notice must be given to all parties "
            "and to the deponent. "
            "(c) Scope: The scope of examination is the same as would be allowed "
            "at trial, including cross-examination. "
            "(d) Use at Trial: A deposition may be used at trial for impeachment "
            "or, if the witness is unavailable (as defined in Rule 804 of the "
            "Arizona Rules of Evidence), as substantive evidence. "
            "(e) Defendant's Presence: The defendant has the right to be present "
            "at any deposition taken by the state. "
            "(f) Limitations: The court may limit depositions upon a showing that "
            "the deposition would cause unreasonable annoyance, embarrassment, "
            "oppression, burden, or expense. "
            "Strategic significance: Criminal depositions in Arizona are a "
            "powerful discovery tool — defense counsel can lock in witness "
            "testimony, identify inconsistencies, and preserve testimony for "
            "Confrontation Clause purposes."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Criminal Procedure",
    },
    {
        "code": "ARIZ R CRIM P 17",
        "title": "Plea Agreements",
        "text": (
            "Arizona Rule of Criminal Procedure 17 (Pleas and Plea Agreements — "
            "formerly Rule 17 / Rule 19.1). Key provisions: "
            "(a) Types of Pleas: A defendant may plead not guilty, guilty, or "
            "no contest (nolo contendere). A no contest plea has the same effect "
            "as a guilty plea but cannot be used as an admission in subsequent "
            "civil proceedings. "
            "(b) Plea Agreements: The prosecutor and defense counsel may negotiate "
            "a plea agreement. Common types include: (1) Charge bargain — the "
            "defendant pleads to a lesser offense; (2) Sentence bargain — the "
            "state agrees to recommend or stipulate to a specific sentence; "
            "(3) Count bargain — the state agrees to dismiss some charges; "
            "(4) Stipulated facts — the parties agree to certain facts relevant "
            "to sentencing. "
            "(c) Court's Role: The court is not bound by the plea agreement. "
            "The court must determine that the plea is voluntary, that the "
            "defendant understands the rights being waived and the consequences "
            "of the plea, and that there is a factual basis for the plea. "
            "(d) Withdrawal: A defendant may withdraw a guilty plea before "
            "sentencing if the court finds it is fair and just to allow "
            "withdrawal. After sentencing, withdrawal is permitted only upon "
            "a showing of manifest injustice. "
            "(e) Conditional Plea: Under certain circumstances, a defendant may "
            "enter a conditional plea of guilty, reserving the right to appeal "
            "a specified pre-trial ruling (e.g., denial of a motion to suppress). "
            "If the appeal is successful, the defendant may withdraw the plea."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Criminal Procedure",
    },
    {
        "code": "ARIZ R CRIM P 20",
        "title": "Motion for Judgment of Acquittal",
        "text": (
            "Arizona Rule of Criminal Procedure 20 (Judgment of Acquittal). "
            "(a) Motion at Close of State's Case: After the state has rested its "
            "case-in-chief, the court on the defendant's motion shall enter a "
            "judgment of acquittal on any offense charged in the indictment or "
            "information as to which the evidence is insufficient to sustain a "
            "conviction. The court may also enter a judgment of acquittal on its "
            "own motion. "
            "(b) Standard: The court must determine whether, viewing the evidence "
            "in the light most favorable to the state and drawing all reasonable "
            "inferences in the state's favor, substantial evidence exists to "
            "support a finding of guilt beyond a reasonable doubt. 'Substantial "
            "evidence' is evidence that reasonable persons could accept as adequate "
            "and sufficient to support a conclusion of guilt beyond a reasonable "
            "doubt. "
            "(c) Renewed Motion After Verdict: If the jury returns a guilty "
            "verdict, the defendant may renew the motion for judgment of acquittal "
            "within the time for filing a motion for new trial. "
            "(d) Conditional Ruling: If the court grants the renewed motion, it "
            "must also conditionally rule on any pending motion for new trial "
            "by determining whether a new trial should be granted if the judgment "
            "of acquittal is reversed on appeal. "
            "Strategic significance: Rule 20 is the primary mechanism for "
            "challenging the sufficiency of the prosecution's evidence at trial. "
            "It preserves the issue for appellate review. Failure to move for "
            "Rule 20 acquittal at the close of the state's case may waive the "
            "issue on appeal (review only for fundamental error)."
        ),
        "category": "procedural",
        "jurisdiction": "AZ",
        "severity": "PROCEDURAL",
        "source": "Arizona Rules of Criminal Procedure",
    },
]


# ============================================================================
# SEEDER FUNCTIONS
# ============================================================================

def seed_brain(dry_run: bool = False) -> dict:
    """Seed the Diamond Brain with all ARS criminal law citations.

    Args:
        dry_run: If True, print entries without writing to brain.

    Returns:
        Summary dict with counts per category and total.
    """
    brain = DiamondBrain()
    category_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    total = 0

    for entry in ARS_CITATIONS:
        code = entry["code"]
        title = entry["title"]
        text = entry["text"]
        category = entry["category"]
        jurisdiction = entry.get("jurisdiction", "AZ")
        severity = entry.get("severity", "REFERENCE")
        source = entry.get("source", "ARS research")

        if dry_run:
            preview = text[:90].replace("\n", " ") + "..."
            print(f"  [{severity:<15}] {code:<25} {title}")
            print(f"                    {preview}")
            print()
        else:
            brain.cite(
                code=code,
                title=title,
                text=text,
                category=category,
                jurisdiction=jurisdiction,
                severity=severity,
                source=source,
            )

        category_counts[category] = category_counts.get(category, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        total += 1

    return {
        "total_citations_seeded": total,
        "categories": category_counts,
        "severities": severity_counts,
        "unique_categories": len(category_counts),
        "dry_run": dry_run,
    }


def print_summary(result: dict) -> None:
    """Print seeding summary."""
    mode = "DRY RUN" if result["dry_run"] else "SEEDED"

    print()
    print("=" * 70)
    print(f"  ARIZONA CRIMINAL LAW SEEDER — {mode}")
    print("=" * 70)
    print()
    print(f"  Total citations {mode.lower()}: {result['total_citations_seeded']}")
    print(f"  Unique categories        : {result['unique_categories']}")
    print()
    print("  By category:")
    print("  " + "-" * 50)
    for cat, count in sorted(result["categories"].items()):
        bar = "|" * (count * 2)
        print(f"    {cat:<20} {count:>3}  [{bar}]")
    print()
    print("  By severity:")
    print("  " + "-" * 50)
    for sev, count in sorted(result["severities"].items()):
        bar = "|" * (count * 2)
        print(f"    {sev:<20} {count:>3}  [{bar}]")
    print()


def print_post_seed_stats() -> None:
    """Print brain citation statistics after seeding."""
    brain = DiamondBrain()
    stats = brain.citation_stats()

    print()
    print("=" * 70)
    print("  DIAMOND BRAIN — POST-SEED CITATION STATISTICS")
    print("=" * 70)
    print()
    print(f"  Total citations in brain : {stats.get('total_citations', 0)}")
    print()

    if stats.get("by_category"):
        print("  By category:")
        print("  " + "-" * 60)
        for cat, count in sorted(stats["by_category"].items()):
            bar = "|" * min(count * 2, 40)
            print(f"    {cat:<20} {count:>3} citations  [{bar}]")
        print()

    if stats.get("by_severity"):
        print("  By severity:")
        print("  " + "-" * 60)
        for sev, count in sorted(stats["by_severity"].items()):
            bar = "|" * min(count * 2, 40)
            print(f"    {sev:<20} {count:>3} citations  [{bar}]")
        print()

    if stats.get("by_jurisdiction"):
        print("  By jurisdiction:")
        print("  " + "-" * 60)
        for jur, count in sorted(stats["by_jurisdiction"].items()):
            print(f"    {jur:<10} {count:>3} citations")
        print()

    # Sample recall tests
    print("  Sample citation recalls:")
    print("  " + "-" * 60)
    test_queries = [
        "ARS 13-1105",
        "ARS 13-404",
        "ARS 28-1381",
        "ARIZ R EVID 403",
        "AZ CONST ART 2 SEC 10",
    ]
    for q in test_queries:
        results = brain.recall_citations(query=q, max_results=1)
        if results:
            r = results[0]
            text_preview = r["text"][:70] + "..." if len(r["text"]) > 70 else r["text"]
            print(f"    {r['code']:<25} [{r['severity']}] {r['title']}")
            print(f"      -> {text_preview}")
        else:
            print(f"    (no results for '{q}')")
    print()


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        result = seed_brain(dry_run=True)
        print_summary(result)
    elif "--stats" in sys.argv:
        print_post_seed_stats()
    else:
        result = seed_brain(dry_run=False)
        print_summary(result)
        print_post_seed_stats()
