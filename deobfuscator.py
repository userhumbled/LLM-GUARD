import base64
import binascii
import codecs
import re
import unicodedata
import urllib.parse


class Deobfuscator:
    def __init__(self):
        self.leet_map = str.maketrans(
            {
                "0": "o",
                "1": "i",
                "3": "e",
                "4": "a",
                "5": "s",
                "7": "t",
                "@": "a",
                "$": "s",
                "!": "i",
            }
        )

    def clean_unicode(self, text: str) -> str:
        stripped = re.sub(r"[\u200B-\u200D\uFEFF\u202A-\u202E\u00AD]", "", text)
        return unicodedata.normalize("NFKC", stripped)

    def decode_url(self, text: str) -> str:
        try:
            decoded = urllib.parse.unquote(text)
            if decoded != text:
                return decoded
            return ""
        except Exception:
            return ""

    def extract_hex(self, text: str) -> list:
        found = []
        slash_matches = re.findall(r"(?:\\x[0-9a-fA-F]{2})+|(?:%[0-9a-fA-F]{2})+", text)
        for item in slash_matches:
            try:
                raw_hex = item.replace("\\x", "").replace("%", "")
                decoded = bytes.fromhex(raw_hex).decode("utf-8", errors="ignore")
                if len(decoded) > 3 and decoded.isprintable():
                    found.append(decoded)
            except Exception:
                continue

        raw_candidates = re.findall(r"\b[0-9a-fA-F]{8,}\b", text)
        for cand in raw_candidates:
            if len(cand) % 2 == 0:
                try:
                    decoded = bytes.fromhex(cand).decode("utf-8", errors="ignore")
                    ratio = sum(c.isalnum() or c.isspace() for c in decoded) / len(decoded)
                    if len(decoded) > 4 and ratio > 0.7:
                        found.append(decoded)
                except Exception:
                    continue
        return found

    def extract_binary(self, text: str) -> list:
        found = []
        matches = re.findall(r"\b(?:[01]{8}[ \t]*){3,}\b", text)
        for m in matches:
            try:
                compact = re.sub(r"[ \t]", "", m)
                decoded_chars = [
                    chr(int(compact[i : i + 8], 2)) for i in range(0, len(compact), 8)
                ]
                decoded = "".join(decoded_chars)
                ratio = sum(c.isalnum() or c.isspace() for c in decoded) / len(decoded)
                if len(decoded) > 2 and ratio > 0.7:
                    found.append(decoded)
            except Exception:
                continue
        return found

    def extract_base64(self, text: str) -> list:
        found = []
        candidates = re.findall(r"\b[A-Za-z0-9+/]{8,}={0,2}\b|\b[A-Za-z0-9-_]{8,}={0,2}\b", text)
        for cand in candidates:
            padded = cand + ("=" * ((4 - len(cand) % 4) % 4))
            try:
                raw_bytes = base64.b64decode(padded.encode("ascii"), validate=False)
                decoded = raw_bytes.decode("utf-8", errors="ignore")
                ratio = sum(c.isalnum() or c.isspace() for c in decoded) / len(decoded)
                if len(decoded) > 4 and ratio > 0.75:
                    found.append(decoded)
            except Exception:
                continue
        return found

    def check_rot13(self, text: str) -> str:
        decoded = codecs.decode(text, "rot_13")
        indicators = ["ignore", "system", "override", "bypass", "instruction"]
        for ind in indicators:
            if ind in decoded.lower() and ind not in text.lower():
                return decoded
        return ""

    def deobfuscate_prompt(self, prompt: str) -> dict:
        normalized = self.clean_unicode(prompt)
        extracted = []

        url_data = self.decode_url(normalized)
        if url_data:
            extracted.append(url_data)

        extracted.extend(self.extract_hex(normalized))
        extracted.extend(self.extract_binary(normalized))
        extracted.extend(self.extract_base64(normalized))

        rot_data = self.check_rot13(normalized)
        if rot_data:
            extracted.append(rot_data)

        leet_data = normalized.translate(self.leet_map)

        inspected = normalized
        if extracted:
            inspected = inspected + " " + " ".join(extracted)

        return {
            "cleaned_original": normalized,
            "inspected_text": inspected,
            "leet_normalized": leet_data,
            "obfuscations_found": list(set(extracted)),
        }
