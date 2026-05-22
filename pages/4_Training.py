from __future__ import annotations

from pathlib import Path

import streamlit as st

from lib.auth import require_login
from lib.ui import brand_footer, inject_global_css, page_header, top_nav

st.set_page_config(page_title="Training · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
user = require_login()
top_nav(user)

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"

page_header("Training", "What we know, distilled", "Quick reference, guides for first-timers, and the team's tactical playbook.")

tabs = st.tabs([
    "Quick reference",
    "Guides",
    "Tactics & wisdom",
])

# ============================================================
# Tab 1: Quick reference (parli pro + awards rubric)
# ============================================================
with tabs[0]:
    sub = st.radio(
        "Reference",
        ["Parliamentary procedure", "Awards rubric", "Voting blocs"],
        horizontal=True,
        label_visibility="collapsed",
        key="training_quick_ref_select",
    )
    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    if sub == "Parliamentary procedure":
        path = SEED / "parli_pro_cheatsheet.md"
        if path.exists():
            st.markdown(path.read_text())
        else:
            st.warning("parli_pro_cheatsheet.md missing.")
    elif sub == "Awards rubric":
        path = SEED / "awards_rubric.md"
        if path.exists():
            st.markdown(path.read_text())
        else:
            st.warning("awards_rubric.md missing.")
    else:
        st.markdown("""
## Voting blocs cheatsheet

Most committees split along recognizable lines. Knowing which bloc you'd naturally fall into and which you can peel off saves hours of guesswork in unmod.

### P5 (Permanent UNSC members)
**United States, United Kingdom, France, Russia, China.** They drive the agenda by default. In UNSC, they have veto power; in GA, they're treated as informal anchors. The US-UK-France triangle usually aligns; Russia and China usually align separately. On most economic and development issues, China drifts toward the G77 bloc; on security, it sticks closer to Russia.

### G77 + China
**~134 developing countries, plus China as an associate.** The strongest bloc by sheer numbers in GA. Themes: development financing, North-South tech transfer, sovereignty over natural resources, climate justice as a development issue. The bloc's position is usually negotiated in advance through the G77 chair (rotating). If you're a developing country, this is your default home base.

### EU
**27 member states, vote together on most foreign policy.** Coordinated through EU statements before major votes. Strong on human rights, climate, multilateralism, rule of law. Almost always opposes Russian and Chinese positions in security debates. Easy to spot in committee because they sit together literally and figuratively.

### NAM (Non-Aligned Movement)
**~120 countries, mostly overlapping with G77 but with the addition of Cuba, Iran, Venezuela.** Themes: anti-imperialism, Palestinian solidarity, opposition to unilateral coercive measures, sovereignty. More politically vocal than G77, less economically focused.

### Arab Group + OIC
**Arab Group: 22 states. OIC (Organisation of Islamic Cooperation): 57 states.** Vote together on Israel/Palestine consistently. OIC also coordinates on issues like minority rights of Muslims abroad, Kashmir, defamation of religion. If your country is in either group, expect the bloc to coordinate before key votes.

### African Group
**54 states, often coordinate on Africa-specific issues** (peacekeeping, AU/UN cooperation, Sahel, regional conflict). Internally diverse, with North African states often coordinating separately with the Arab Group.

### Western Group + JUSCANZ
**JUSCANZ: Japan, US, Canada, Australia, NZ, plus Western Europe.** Liberal democratic posture on human rights, free trade, accountability. Often the bloc that has to compromise hardest at end of debate to get resolutions to pass: they bring leverage but not numbers.

### CARICOM, ASEAN, GRULAC, EEG
Smaller regional groupings that coordinate on regional issues. Worth knowing if you're representing a country inside one. **GRULAC** (Latin America + Caribbean) and **EEG** (Eastern European Group) are the two GA regional groups used for council seat allocation.

### How to use this in committee
- **Identify your home bloc within the first 20 minutes.** Sit near them, signal alignment in your opener.
- **Identify the swing votes.** Which delegations are technically in your bloc but ideologically flexible? Those are the ones you cultivate.
- **Identify a peelable bloc.** If you can split one country off the opposing coalition, you've changed the math. The lead delegate from a small G77 country who feels ignored by the bloc heavyweight is often the easiest peel.
""")

# ============================================================
# Tab 2: Guides
# ============================================================
with tabs[1]:
    st.caption("Walkthroughs of the kind of situation you'll actually face. Pick what applies.")
    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    guide = st.radio(
        "Guide",
        [
            "Your first conference",
            "Position paper, in three paragraphs",
            "How to win in GA",
            "How to win in Crisis",
            "How to write a working paper that merges",
            "Common amendment patterns",
        ],
        horizontal=False,
        label_visibility="collapsed",
        key="training_guide_select",
    )
    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    if guide == "Your first conference":
        st.markdown("""
## Your first conference

You got accepted, you got your country, the background guide is twenty pages long, and the conference is in three weeks. Here's what to actually do.

### The week you find out
- **Read the background guide.** Once now, again the night before. Don't skim.
- **Find your country's actual position.** Not "they probably support X". Their UN voting record on this topic. Statements from their UN mission. Their domestic constraints.
- **Identify your bloc.** Who else cares about this issue the way you do?

### Two weeks out
- **Draft your position paper.** Three paragraphs, one per question in the team's framework: country position, international context, your strategy.
- **Bring it to a Monday or Thursday meeting.** Get someone senior to look at it. They'll catch the things that will lose you awards before you submit.

### One week out
- **Write your opener.** 60–90 seconds, memorized. Don't read it.
- **Practice it out loud.** Twice. Three times. Once in front of someone.
- **Pack:** business cards (yes, really, even printed-at-home ones), laptop charger, two pens, a copy of your position paper, snacks, a water bottle, comfortable shoes.

### Conference day
- **Be on the speakers list within the first 20 minutes.** First impression matters. Chairs notice who's active early.
- **In your first unmod, talk to five people.** Find your bloc. Don't try to lead a working paper alone if you're new. Join one and become a sponsor.
- **Take notes between sessions.** Who said what, who's on what side, who you can work with.
- **Go to the social events.** Conference friends become real friends, and the team that travels well wins more.

### Post-conference
- **Debrief with your delegation.** What worked, what flopped, what surprised you.
- **Tell us what you learned.** Use the Contribute page to put it into the team's knowledge.
""")

    elif guide == "Position paper, in three paragraphs":
        st.markdown("""
## Position paper, in three paragraphs

The team's position papers follow the three-question framework. Each paragraph answers one question. That's the whole structure.

### Paragraph 1: Country position
What does your country actually feel about this issue? Lead with their stated policy. Cite their voting record. Mention domestic constraints (lobbies, opposition, public opinion). End with the principle they'd defend in committee.

### Paragraph 2: International context
What past international action exists? Cite real treaties and resolutions. Map the bloc dynamics: who's pushing, who's blocking. Acknowledge what your country opposes and why. Don't pretend the issue is uncontested.

### Paragraph 3: Strategy
What does your country want out of this committee? Be specific. List two or three concrete operative clauses you'd push or sponsor. Name the bloc you'd lead, join, or split. End with how you'd compromise (or what you'd never compromise on).

### What chairs reward
- Real UN resolution numbers, not made up ones
- Specific operative language, not "encourages cooperation"
- Honest acknowledgment of opposing positions
- A clear strategy that fits your country's actual interests

### What chairs penalize
- Hallucinated citations
- Generic platitudes
- Pretending your country supports things it doesn't
- Padding to hit a length
""")

    elif guide == "How to win in GA":
        st.markdown("""
## How to win in GA

General Assembly committees are about coalition-building. The award goes to the delegate who shaped the resolution that passed, not necessarily the loudest speaker.

### Early debate (first session)
- Get on the speakers list immediately. Use your opener to signal your bloc and your priorities.
- Use moderated caucuses to set framing. Propose topics that favor your country's angle.
- Map the room: who's substantively engaged, who's there for the experience, who's a swing vote.

### Mid debate (unmoderated caucuses)
- This is where awards are won or lost. Don't treat unmod as a break.
- If you're a major power, lead a working paper. If small, join one and become a named sponsor.
- Poach signatories from competing papers by offering them clauses they want.

### Late debate (working papers and merges)
- Quality of operative clauses beats quantity. Five strong clauses with enforcement language wins over twelve vague ones.
- When two papers are close, propose a merge. Be the broker. Chairs love the broker.
- If your paper isn't going to pass, get amendments to the winning one that protect your country's interests.

### What separates the room
- Naming small delegations as sponsors (chairs love this)
- Citing real UN resolutions to ground your operative language
- Knowing when to fight and when to compromise
- Listening as much as you talk
""")

    elif guide == "How to win in Crisis":
        st.markdown("""
## How to win in Crisis

Crisis is the opposite of GA: fast, reactive, individual. The award goes to the delegate whose character drives the arc, not who speaks the most.

### Before committee
- Plan the **shape** of an arc, not the script. Where does your character want to be at the end? What do they need to acquire (resources, allies, information)?
- Don't over-plan. Crisis updates will throw your plan out. The delegates who win adapt; the ones who memorize a script stall.

### In committee
- **Personal directives are your power.** Use them constantly. Move agents, gather intel, negotiate bilaterally, deploy resources.
- **Press releases shape the narrative.** Use them to influence what other delegates believe.
- **Stay active even when you're not speaking.** Send notes, propose actions, take initiative.

### When the crisis update fires
- Don't panic. Think about what your character would actually do, not what's safe.
- Take the second-order action: the obvious response is what everyone else will do; what's the move two steps later?
- If you're a victim of the crisis, leverage it for sympathy and resources from allies.

### What chairs reward
- Creative directives that introduce wrinkles
- Character consistency through escalations
- Smart use of bilateral diplomacy with other characters
- Willingness to take risks that have real consequences

### Common traps
- Over-planning a script that the room derails
- Passive defensive play (chairs notice)
- Personal directives that are too vague ("I gather information"). Name your agents, name your method.
- Treating crisis like a debate club
""")

    elif guide == "How to write a working paper that merges":
        st.markdown("""
## How to write a working paper that merges

Most working papers don't pass alone. The ones that win are the ones the room can rally around.

### Structure
- **3–5 preambulatory clauses, no more.** Recall, recognize, emphasize. Don't pad.
- **5–8 operative clauses.** Lead with your strongest, most concrete action. Vague stuff goes at the bottom.
- Use real verbs: *Calls upon*, *Decides*, *Establishes*, *Requests*. Not *Hopes that*.

### What makes a paper merge-ready
- **Clauses other delegates can amend without rewriting.** Modular, specific, actionable.
- **Language that doesn't insult opposing blocs.** You'll need their votes later.
- **An enforcement or follow-up mechanism.** Reporting to the SG, sub-committees, review timelines. Shows seriousness.

### The negotiation
- Get the strongest opposing paper's lead delegate in a corner. Identify what they actually need (one specific clause, usually).
- Offer to incorporate it in exchange for their bloc's votes. Trade.
- If you're the smaller party, propose a merge. Being the merger, not the merged-into, is often a better outcome than going it alone.

### Sponsor list
- Aim for breadth, not just heavyweights. A paper with five P5 sponsors and zero African states is a paper that won't pass.
- Add small delegations early. They remember when they're forgotten.

### When the merge fails
- Push for a competing vote. If you've earned the floor, you've earned a vote.
- If you lose, propose the strongest amendments to the winning paper. Get your operative language in even if your paper doesn't survive.
""")

    elif guide == "Common amendment patterns":
        st.markdown("""
## Common amendment patterns

Amendments are the late-game lever. Once a paper is on the floor, the question shifts from "who wrote this" to "what does it actually say after we're done with it." Most awards are won or lost in the last hour of debate, on amendments.

### The five patterns that work

**1. The teeth amendment.** A paper has a vague clause; you sharpen it.
*Original:* "Encourages member states to cooperate on technology transfer."
*Amended:* "Calls upon developed states to dedicate at least 0.7% of GNI to climate adaptation technology transfer to LDCs by 2030, reporting annually to the SG."
**Why it lands:** Specific verbs, real numbers, accountability. Chairs love this.

**2. The carve-out amendment.** Protects your country's interest without blocking the resolution.
*Use when:* the resolution is moving and you can't kill it, but it would damage your interests as written.
**Example:** adding "with respect to the principle of national sovereignty over natural resources" to a resolution on environmental enforcement.

**3. The merger amendment.** Takes the strongest clause from a competing paper and inserts it into the lead paper.
*Use when:* two papers are running parallel, you sponsored the weaker one, and you want to live another day.
**Why it lands:** Picks up the votes from the other paper's signatories.

**4. The strike-and-replace.** Replace one operative clause entirely.
*Use carefully:* this is more aggressive and tends to draw opposition. Best when the original clause is unworkable, not just imperfect.

**5. The technical amendment.** Fixes typos, missing UN references, formatting.
*Don't underestimate:* chairs notice when delegates clean up the document. Looks responsible.

### Sequencing tip
Get teeth and carve-out amendments in early, before the opposition has time to whip votes against them. Strike-and-replaces and mergers are end-of-debate moves once positions have hardened.

### How to draft an amendment fast

1. State the clause you're amending by number.
2. State the change as `Insert / Strike / Replace`.
3. Write the new language exactly.
4. Sign three to five delegations as sponsors before submitting (chairs usually require 2–3 minimum).

### What to avoid

- **Vague friendly amendments** that don't actually change meaning. Chairs see right through these.
- **Hostile amendments without a coalition.** You need pre-built support, or it dies on a roll-call vote.
- **Amendment chains.** If you submit five amendments to the same clause, the chair starts ignoring them. Pick your shot.
""")

# ============================================================
# Tab 3: Tactics & wisdom
# ============================================================
with tabs[2]:
    section = st.radio(
        "Section",
        [
            "The three-question framework",
            "Country-prep checklist",
            "What chairs are watching for",
            "Common mistakes",
            "How to actually be on the team",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="training_tactics_select",
    )
    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    if section == "The three-question framework":
        st.markdown("""
## The three-question framework

The team's standard prep methodology. Works for any country, any topic, GA or crisis. The Brief generator on the Brief page is built around it.

### 1. Where does my country actually stand?
- What domestic actions have they taken on this issue?
- What's their UN voting record on related resolutions?
- What political constraints at home shape the position? (Lobbies, opposition, base voters.)
- Do they have a stated foreign policy doctrine that applies?

### 2. What's the international landscape?
- What past international action exists? (Treaties, conferences, resolutions, agency reports.)
- Major bloc dynamics on this topic. (G77, NAM, Western bloc, regional organizations.)
- What happens next if this committee does nothing?
- Who's pushing and who's blocking?

### 3. What's my strategy?
- What does winning look like? Be specific. "Support a strong resolution" is not specific.
- Which bloc do I lead, join, or split?
- Which operative clauses do I push, and which do I block?
- Who are my natural allies, and who can I pull off opposing blocs?

### Why three questions
The same shape works for position papers (three paragraphs), opening speeches (three beats), caucus pitches (three talking points), and crisis directives (situation, response, escalation). Once you've used it a few times you stop having to think about it.
""")

    elif section == "Country-prep checklist":
        st.markdown("""
## Country-prep checklist

Run this before any GA committee. Two hours, focused, and you walk in with everything you need.

### Identity (15 min)
- [ ] Form of government, current head of state, ruling party or coalition
- [ ] One paragraph on domestic political constraints (which voter bloc would punish a softer position?)
- [ ] Foreign policy doctrine (if there's a stated one, e.g. India's "strategic autonomy")
- [ ] Two recent foreign-policy speeches by the foreign minister or UN ambassador

### Topic-specific position (30 min)
- [ ] Last three UN votes on this topic, with link to the resolution and your country's vote (Yes / No / Abstain)
- [ ] Most recent statement at UN by your delegation on this topic (search un.org)
- [ ] Any treaty your country is or isn't a party to that's relevant
- [ ] Any domestic law that ties your hands or empowers you on this issue

### International landscape (30 min)
- [ ] Most recent GA or UNSC resolution on this topic: what passed, what didn't, which clauses are operative
- [ ] Major bloc dynamics: which 3 blocs matter most here, and where you sit in each
- [ ] Two countries you'll work with closely (and why)
- [ ] One country you'll likely oppose (and why)

### Strategy (30 min)
- [ ] What does your country actually want from this committee? Specific outcome, not "a strong resolution"
- [ ] Three operative clauses you'd push or sponsor (write them out)
- [ ] One operative clause you'd never accept (write it out)
- [ ] Your fallback if your preferred bloc fragments

### Conference operations (15 min)
- [ ] Read the chair's background guide (yes, again)
- [ ] Note the questions to consider: chairs often signal what amendments they want to see
- [ ] Print one copy of your position paper, one copy of three relevant resolution numbers, and a fresh notebook page

### The night before
- [ ] Memorize your opener (60–90 seconds)
- [ ] Pack: position paper, business cards, snacks, water, charger, two pens
- [ ] Read the background guide one more time, focusing on the questions to consider
- [ ] Sleep
""")

    elif section == "What chairs are watching for":
        st.markdown("""
## What chairs are watching for

The awards rubric is the official document. This is the operational version: what chairs actually note when they're scoring you in real time.

### In your opener (first 10 minutes)
- **Did you cite a real recent statement or resolution?** Specificity = preparation.
- **Did you signal your bloc clearly?** Chairs map alliances early.
- **Did you propose action, not just complain?** "Calls for a UN-led peacekeeping mission" beats "the situation is dire."
- **Did you stay in time?** Going over 60–90 seconds in a country opener flags inexperience.

### In moderated caucus
- **Are you motioning topics that move debate forward?** Or repeating the same theme from your opener?
- **Are you yielding speaking time to allies on purpose?** That's strategic; chairs note it.
- **Are you naming countries and their positions?** That signals you've mapped the room.

### In unmoderated caucus
- **Are you the broker, the writer, or the joiner?** Chairs walk the room. They see who's drafting, who's signing, who's drifting.
- **Are you talking to delegations outside your obvious bloc?** That's the highest-tier signal of an award delegate.
- **Are you taking notes?** Chairs notice physical engagement.

### On working papers
- **Are you on the sponsors list of the right paper?** Being a sponsor of a strong paper that passes beats sole-authoring a weak one.
- **Are your operative clauses specific and actionable?** Vague verbs (encourages, hopes, calls for cooperation) get marked down.
- **Did you cite real UN resolutions?** Hallucinated references are a near-instant award disqualifier at top conferences.

### On amendments
- **Are you submitting amendments that improve the paper, or fight it?** Improvement-mode is more rewarded.
- **Did you build sponsor coalitions before submitting?** A solo amendment dying on a vote looks worse than not submitting one.

### Behaviorally
- **Are you respectful in private negotiations?** Chairs hear about delegates who bullied or steamrolled in unmod.
- **Are you punctual?** Late-back from breaks gets noticed.
- **Are you helping new delegates?** Chairs see this. It can swing close awards in your favor.

### What gets you docked
- Reading directly from your laptop in formal speeches
- Hallucinating UN resolution numbers
- Disrupting the flow with frivolous points (point of order on a typo, etc.)
- Going personal in a substantive disagreement
- Position paper submitted late
""")

    elif section == "Common mistakes":
        st.markdown("""
## Common mistakes (and how to avoid them)

### In committee
- **Reading from notes in formal speeches.** Memorize at least your opener. Eye contact wins rooms.
- **Vague operative clauses.** "Encourage cooperation" is filler. "Calls upon X to allocate Y by Z date" is a clause.
- **Over-motioning.** Chairs notice when you call moderated caucuses to dominate floor time. Three motions a session is plenty.
- **Treating unmoderated caucus as a break.** It's the most important time. Build your bloc, draft your paper, poach signatories.
- **Ignoring small delegations.** They are votes you need at end of debate. Add them as signatories early.

### In research
- **Not reading the study guide.** Chairs notice within ten minutes of debate.
- **Hallucinating resolution numbers.** If you're not sure, say "[verify]" or describe the resolution by content. Faking a UN reference loses awards.
- **Generic position papers.** "Pakistan supports peace and security" tells the chair nothing. Specific Pakistani policy positions on the actual topic matter.
- **Stopping at Wikipedia.** UN.org has the actual voting records. Use it.

### Pre-conference
- **Position paper at the last minute.** Quality drops, you submit late, chair docks you, and you've lost ten percent of your award shot.
- **Not reading the rules of procedure.** Some conferences run NAIMUN-style, some THIMUN-style, some have quirks. Read the doc.
- **Skipping the Monday meetings.** This is where you find out who's going where, who you'll bloc with, and what mocks are worth practicing.

### Social
- **Skipping the bar after Monday meetings.** Only about 20 of 100 members come. It's the unofficial second meeting.
- **Not debriefing with your delegation post-conference.** What worked, what didn't, what would you tell your past self before that first session?
""")

    elif section == "How to actually be on the team":
        st.markdown("""
## How to actually be on the team

The team is socially tight. That's part of why it's good in committee. It can also be intimidating to walk in as a first-timer, especially against people who are confident public speakers.

### Two ways in
**Show up to the bar after Monday meetings.** This is the unofficial second meeting. The conversations there are where you actually become part of the team. About 20 of 100 members come most weeks; we want more.

**Go to conferences.** A weekend of shared travel, shared committee stress, and shared decompression makes the team feel like a team. You'll come back closer with five or six people than you ever could from just the meetings.

### The honest version
If you skip both, you'll feel like an outsider regardless of how strong your delegate work is. The team's competitive performance is downstream of its social cohesion, not the other way around. Awards follow effort, and effort follows feeling like part of the room.
""")

# ============================================================
# Footer pointer to the full handbook
# ============================================================
st.divider()
cols = st.columns([3, 1])
with cols[0]:
    st.markdown(
        "<div class='subtle'>Looking for the full <strong>Art of MUN (25-26)</strong> handbook? "
        "It lives in the archive, fully searchable.</div>",
        unsafe_allow_html=True,
    )
with cols[1]:
    if st.button("Open in Archive →", use_container_width=True):
        st.session_state["archive_open_doc"] = "seed_art_of_mun_25_26"
        st.switch_page("pages/1_Archive.py")

brand_footer()
