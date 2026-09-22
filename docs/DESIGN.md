# Reading-first design — September 22, 2026

“Looks AI-generated” is a perception, not a reliable test of authorship. The useful question is which repeated design decisions make this particular product feel generic or get in the reader’s way.

**What the research supports**

Anthropic reports that unguided frontend generation tends toward predictable layouts. Its design evaluation specifically criticizes default components and purple gradients over white cards. This is practitioner evidence about model behavior, not a universal rule that cards or purple are bad. [Anthropic’s engineering report](https://www.anthropic.com/engineering/harness-design-long-running-apps).

Nielsen Norman Group explains that unnecessary interface information competes with the content users need. Minimalism should preserve useful controls, rather than removing them to achieve a particular look. [Aesthetic and minimalist design](https://www.nngroup.com/articles/aesthetic-minimalist-design/).

Progressive disclosure puts common tasks first and moves less frequent options to a secondary view. It should make complexity manageable without making important functionality undiscoverable. [Progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/).

**Applied to this newsletter**

The previous layout repeated marketing slogans, decorated every story as a card, used colored importance badges, and duplicated titles in a sidebar. Those elements made the interface more prominent than the newsletter. That is our assessment of this page, informed by the research and the user’s feedback.

The replacement removes the hero, slogans, decorative logo mark, cards, shadows, colored badges, contents sidebar and reading-budget widget. Stories form one continuous column with restrained type and thin section rules. Source accounts form a plain list. System typography remains: changing fonts alone would not solve the reading problem or justify another dependency.

The primary action is **New briefing**. Period, archive and separate collection controls are under **Options & archive**. Sources and Settings remain directly accessible. Evidence stays beside each story; missing-source counts remain visible because they affect how to interpret the edition.

Functional cleanup preserves form edits after failed saves, prevents duplicate run submissions, avoids overlapping polling requests, retains the selected edition during collection, and shows run errors once. None of these changes connects unavailable social accounts or makes incomplete evidence sufficient.
