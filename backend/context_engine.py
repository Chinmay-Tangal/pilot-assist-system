import json
import ollama
from pydantic import BaseModel, Field
from typing import Optional

# --- Define our Strict JSON Schema ---
# Pydantic forces the LLM to output EXACTLY this structure
class ATCInstruction(BaseModel):
    callsign: Optional[str] = Field(description="The exact spoken callsign, e.g., 'Delta 52'. Do NOT convert to 3-letter ICAO codes.")
    clearance_limit: Optional[str] = Field(description="Destination airport or city. Leave null if not mentioned.")
    departure_procedure: Optional[str] = Field(description="SID or departure route. Leave null if not mentioned.")
    assigned_heading: Optional[int] = Field(description="The assigned magnetic heading as a 3-digit number, e.g., 240")
    assigned_altitude: Optional[str] = Field(description="Any assigned altitude or flight level. Convert words to standard format (e.g., 'flight level 180' -> 'FL180')")
    squawk_code: Optional[str] = Field(description="4-digit transponder code. Leave null if not mentioned.")
    frequency: Optional[str] = Field(description="Radio frequency in strict decimal format, e.g., '119.7'.")
    anomaly_detected: bool = Field(description="True if the instruction implies an emergency or warning. Otherwise false.")

class ContextEngine:
    def __init__(self):
        self.model_name = "llama3.2"
        print(f"Initializing Context Engine with {self.model_name}...")

    def parse_instruction(self, raw_text: str) -> str:
        
        # --- Bulletproof Prompt ---
        system_prompt = """
        You are an expert aviation AI assistant extracting ATC parameters into strict JSON.
        CRITICAL RULES:
        1. CALLSIGN: Use the exact spoken words (e.g., "Delta 52"). Do NOT invent ICAO codes.
        2. HEADING: Extract assigned headings as numbers (e.g., "heading 240" -> 240).
        3. ALTITUDE: Extract ANY altitude mentioned, whether climbing or descending (e.g., "flight level 180" -> "FL180").
        4. FREQUENCY: Convert to numeric decimal format (e.g., "119.7"). If the transcript contains speech-to-text typos like "119 or decimal 7", deduce the intended number ("119.7"). NEVER output text error messages in the JSON.
        5. NULL VALUES: If a parameter is not explicitly spoken, it MUST be null.
        """

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text}
                ],
                format=ATCInstruction.model_json_schema() 
            )
            return response['message']['content']

        except Exception as e:
            print(f"Error communicating with Ollama: {e}")
            return None

if __name__ == "__main__":
    engine = ContextEngine()
    
    # We are using your exact transcription output from earlier
    test_transcription = "Boeing 737, Vilnius Tower. Good morning. You are cleared to London Heathrow via the UPSI-1 Bravo departure, flight planned route. Initially climbed to Flight Level 9 or 0, Squawk 2 6 3 2, departure frequency 1 2 0, decimal 4 5."
    
    print("\n[Raw Whisper Output]:")
    print(test_transcription)
    
    print("\n[Processing with Llama 3.2...]")
    json_result = engine.parse_instruction(test_transcription)
    
    if json_result:
        print("\n[Structured Context Data]:")
        # Prettify the JSON for the terminal
        parsed_data = json.loads(json_result)
        print(json.dumps(parsed_data, indent=4))