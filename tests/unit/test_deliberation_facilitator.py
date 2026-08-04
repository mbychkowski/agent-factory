import unittest
from agent_engine.agents.deliberation_facilitator.agent import root_agent as facilitator_agent
from agent_engine.agents.deliberation_facilitator.schemas import (
    FacilitatorTriageOutput,
    MessageClassification,
    TargetSpecPhase,
)


class TestDeliberationFacilitator(unittest.TestCase):

    def test_facilitator_agent_initialization(self) -> None:
        self.assertEqual(facilitator_agent.name, "deliberation_facilitator")
        self.assertEqual(facilitator_agent.output_schema, FacilitatorTriageOutput)

    def test_facilitator_triage_schema(self) -> None:
        # Test NOISE classification
        noise_output = FacilitatorTriageOutput(
            classification=MessageClassification.NOISE_OFF_TOPIC,
            human_response="Ignored off-topic banter."
        )
        self.assertEqual(noise_output.classification, MessageClassification.NOISE_OFF_TOPIC)
        self.assertEqual(noise_output.target_phase, TargetSpecPhase.NONE)

        # Test ACTIONABLE feedback classification
        actionable_output = FacilitatorTriageOutput(
            classification=MessageClassification.ACTIONABLE_SPEC_FEEDBACK,
            target_phase=TargetSpecPhase.TECHNICAL_DESIGN,
            synthesized_delta="Use Cloud Spanner instead of PostgreSQL for database storage.",
            is_gate_approval=False
        )
        self.assertEqual(actionable_output.classification, MessageClassification.ACTIONABLE_SPEC_FEEDBACK)
        self.assertEqual(actionable_output.target_phase, TargetSpecPhase.TECHNICAL_DESIGN)
        self.assertIn("Cloud Spanner", actionable_output.synthesized_delta)


if __name__ == "__main__":
    unittest.main()
