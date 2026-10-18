import re

class CodeSanitizer:
    """
    Protects game engine tags, formatting codes, and variables from being
    corrupted or mistranslated by AI/Translation engines.
    """
    def __init__(self):
        # Patterns for rich text, unity variables, engine commands, and brackets
        self.patterns = [
            r"<color=[^>]+>", r"</color>",
            r"<size=[^>]+>", r"</size>",
            r"<b>", r"</b>",
            r"<i>", r"</i>",
            r"\[style=[^\]]+\]", r"\[/style\]",
            r"\[accent\]", r"\[/accent\]",
            r"\[[a-zA-Z0-9_\-]+(?:\s+[^\]]+)?\]",  # e.g. [wait 2], [i], [speed 0.5]
            r"\{[a-zA-Z0-9_\-\.%]+\}",              # e.g. {player}, {pop}, {0}, {mg%}
            r"@[a-zA-Z0-9_\-]+(?:\s+.*)?$",         # naninovel @commands
        ]
        self.combined_regex = re.compile("|".join(f"({p})" for p in self.patterns))

    def mask(self, text: str) -> tuple[str, list[str]]:
        """
        Replaces code tags with safe tokens __TAG_0__, __TAG_1__, etc.
        Returns: (masked_text, tags_list)
        """
        tags = []
        def repl(match):
            idx = len(tags)
            tags.append(match.group(0))
            return f"__T{idx}__"

        masked = self.combined_regex.sub(repl, text)
        return masked, tags

    def unmask(self, masked_text: str, tags: list[str]) -> str:
        """
        Restores original code tags back into the translated text.
        """
        result = masked_text
        for idx, tag in enumerate(tags):
            token = f"__T{idx}__"
            # In case the translator added spaces around token: "__ T0 __"
            loose_token = re.compile(rf"__\s*T{idx}\s*__", re.IGNORECASE)
            result = loose_token.sub(tag, result)
        return result
