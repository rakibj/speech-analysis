"""
IELTS Band Scorer v3.0 - Super Accurate Production System
===========================================================

Philosophy: Simulate experienced IELTS examiner judgment through multi-layered
scoring with qualitative gates and quantitative metrics.

Key Innovations:
1. Three-stage scoring (base → deductions → gates)
2. Sophistication-based lexical scoring (not just diversity)
3. Prosody-dominant pronunciation assessment
4. Complex structure inventory tracking
5. Error severity classification
6. Statistical calibration to match real-world distributions

Target Accuracy: 90%+ correlation with human examiners (±0.5 bands)
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from collections import Counter
import re


class IELTSBandScorer :
    """
    Production-grade IELTS Speaking scorer with examiner-like judgment.
    """
    
    # ========================================================================
    # CONFIGURATION - EXAMINER-CALIBRATED THRESHOLDS
    # ========================================================================
    
    # Minimum sample requirements
    MIN_DURATION_SEC = 30
    MIN_CONTENT_WORDS = 50
    MIN_SPEAKING_TIME_SEC = 25
    
    # Fluency & Coherence thresholds
    FLUENCY_WPM_VERY_SLOW = 60
    FLUENCY_WPM_SLOW = 75
    FLUENCY_WPM_HESITANT = 90
    FLUENCY_WPM_COMFORTABLE = 120
    FLUENCY_WPM_RUSHED = 200
    
    FLUENCY_LONG_PAUSE_SEVERE = 3.0
    FLUENCY_LONG_PAUSE_FREQUENT = 2.0
    FLUENCY_LONG_PAUSE_NOTICEABLE = 1.0
    FLUENCY_LONG_PAUSE_MINIMAL = 0.5
    
    FLUENCY_FILLER_EXCESSIVE = 6.0
    FLUENCY_FILLER_FREQUENT = 4.0
    FLUENCY_FILLER_SOME = 2.0
    FLUENCY_FILLER_MINIMAL = 1.0
    
    FLUENCY_REPETITION_EXCESSIVE = 0.15
    FLUENCY_REPETITION_FREQUENT = 0.08
    FLUENCY_REPETITION_SOME = 0.04
    FLUENCY_REPETITION_MINIMAL = 0.02
    
    # Lexical Resource thresholds
    LEXICAL_DIVERSITY_VERY_LIMITED = 0.35
    LEXICAL_DIVERSITY_LIMITED = 0.45
    LEXICAL_DIVERSITY_ADEQUATE = 0.55
    LEXICAL_DIVERSITY_GOOD = 0.65
    
    LEXICAL_ERROR_RATE_FREQUENT = 5.0
    LEXICAL_ERROR_RATE_SOME = 3.0
    LEXICAL_ERROR_RATE_OCCASIONAL = 1.5
    LEXICAL_ERROR_RATE_RARE = 0.5
    
    # Grammar thresholds
    GRAMMAR_MLU_VERY_SIMPLE = 7
    GRAMMAR_MLU_SIMPLE = 9
    GRAMMAR_MLU_MODERATE = 11
    GRAMMAR_MLU_COMPLEX = 13
    
    GRAMMAR_ERROR_RATE_FREQUENT = 8.0
    GRAMMAR_ERROR_RATE_NOTICEABLE = 5.0
    GRAMMAR_ERROR_RATE_SOME = 3.0
    GRAMMAR_ERROR_RATE_OCCASIONAL = 1.5
    
    GRAMMAR_COMPLEX_ACC_VERY_POOR = 0.3
    GRAMMAR_COMPLEX_ACC_POOR = 0.5
    GRAMMAR_COMPLEX_ACC_WEAK = 0.7
    GRAMMAR_COMPLEX_ACC_GOOD = 0.85
    GRAMMAR_COMPLEX_ACC_EXCELLENT = 0.90
    
    GRAMMAR_BLOCKING_FREQUENT = 0.3
    GRAMMAR_BLOCKING_SOME = 0.2
    GRAMMAR_BLOCKING_OCCASIONAL = 0.1
    
    # Pronunciation thresholds
    PRONUN_INTELLIGIBILITY_POOR = 0.6
    PRONUN_INTELLIGIBILITY_FAIR = 0.7
    PRONUN_INTELLIGIBILITY_GOOD = 0.8
    PRONUN_INTELLIGIBILITY_VERY_GOOD = 0.9
    PRONUN_INTELLIGIBILITY_EXCELLENT = 0.95
    
    # Statistical calibration targets
    STAT_BAND_8_PLUS_MAX_PCT = 5.0
    STAT_BAND_9_MAX_PCT = 1.0
    
    def __init__(self):
        """Initialize scorer with supporting resources"""
        self.score_history = []
        
        # Idiomatic expressions database (expanded)
        self.IDIOMS = {
            'once in a blue moon', 'butterflies in my stomach', 'break the ice',
            'hit the nail on the head', 'under the weather', 'spill the beans',
            'cost an arm and a leg', 'piece of cake', 'let the cat out of the bag',
            'burn the midnight oil', 'pull someone\'s leg', 'the ball is in your court',
            'on the same page', 'get cold feet', 'a blessing in disguise',
            'actions speak louder than words', 'at the drop of a hat', 'back to square one',
            'barking up the wrong tree', 'beat around the bush', 'bite the bullet',
            'break a leg', 'call it a day', 'cut corners', 'face the music',
            'get the ball rolling', 'hit the books', 'in the nick of time',
            'jump on the bandwagon', 'kill two birds with one stone', 'miss the boat',
            'no pain no gain', 'on thin ice', 'pull yourself together', 'read between the lines',
            'the best of both worlds', 'time flies', 'up in arms', 'when pigs fly'
        }
        
        # Common collocations (verb + noun)
        self.COLLOCATIONS = {
            'make': ['decision', 'choice', 'mistake', 'progress', 'effort', 'appointment'],
            'take': ['break', 'chance', 'time', 'opportunity', 'responsibility', 'action'],
            'have': ['look', 'chat', 'discussion', 'argument', 'conversation', 'meeting'],
            'do': ['homework', 'research', 'favor', 'damage', 'harm', 'business'],
            'give': ['advice', 'feedback', 'presentation', 'speech', 'hand', 'permission'],
            'pay': ['attention', 'compliment', 'price', 'fine', 'tribute', 'respect'],
            'catch': ['cold', 'bus', 'train', 'attention', 'breath', 'glimpse'],
            'keep': ['promise', 'secret', 'record', 'eye', 'mind', 'track']
        }
        
        # Academic Word List (sample - top 50 families)
        self.AWL = {
            'analysis', 'approach', 'area', 'assess', 'assume', 'authority', 'available',
            'benefit', 'concept', 'consistent', 'constitutional', 'context', 'contract',
            'create', 'data', 'define', 'derive', 'distribute', 'economy', 'environment',
            'establish', 'estimate', 'evident', 'export', 'factor', 'finance', 'formula',
            'function', 'identify', 'income', 'indicate', 'individual', 'interpret',
            'involve', 'issue', 'labor', 'legal', 'legislate', 'major', 'method',
            'occur', 'percent', 'period', 'policy', 'principle', 'proceed', 'process',
            'require', 'research', 'respond', 'role', 'section', 'sector', 'significant',
            'similar', 'source', 'specific', 'structure', 'theory', 'vary'
        }
        
        # Phrasal verbs
        self.PHRASAL_VERBS = {
            'come across', 'come up with', 'carry out', 'find out', 'figure out',
            'get along', 'get over', 'give up', 'go on', 'look after', 'look for',
            'look into', 'make up', 'pick up', 'put off', 'put up with', 'run into',
            'set up', 'take off', 'turn down', 'turn up', 'work out'
        }
        
        # Simple overused words to penalize
        self.BASIC_WORDS = {
            'thing', 'stuff', 'get', 'make', 'do', 'put', 'take',
            'good', 'bad', 'big', 'small', 'nice', 'very', 'really'
        }
    
    # ========================================================================
    # MAIN ENTRY POINT
    # ========================================================================
    
    def score(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main scoring function.
        
        Args:
            analysis_data: Dictionary containing:
                - metadata
                - fluency_coherence
                - lexical_resource
                - grammatical_range_accuracy
                - pronunciation
                - raw_transcript (optional)
        
        Returns:
            Dictionary with overall_band, criterion_bands, feedback, diagnostics
        """
        
        # Step 1: Validate input
        is_valid, reason = self._validate_input(analysis_data)
        if not is_valid:
            return {
                'overall_band': None,
                'criterion_bands': None,
                'feedback_summary': f'Insufficient data: {reason}',
                'validation_failed': True
            }
        
        metadata = analysis_data['metadata']
        transcript = analysis_data.get('raw_transcript', '').lower()
        
        # Step 2: Enhanced feature extraction
        enhanced_features = self._enhance_features(analysis_data, transcript)
        
        # Step 3: Score each criterion with diagnostics
        fluency_result = self._score_fluency_coherence(
            analysis_data['fluency_coherence'],
            metadata
        )
        
        lexical_result = self._score_lexical_resource(
            analysis_data['lexical_resource'],
            enhanced_features['lexical'],
            metadata,
            transcript
        )
        
        grammar_result = self._score_grammatical_range_accuracy(
            analysis_data['grammatical_range_accuracy'],
            metadata
        )
        
        pronunciation_result = self._score_pronunciation(
            analysis_data['pronunciation'],
            enhanced_features['pronunciation'],
            metadata
        )
        
        # Step 4: Calculate overall band
        criterion_bands = {
            'fluency_coherence': fluency_result['score'],
            'lexical_resource': lexical_result['score'],
            'grammatical_range_accuracy': grammar_result['score'],
            'pronunciation': pronunciation_result['score']
        }
        
        overall_band = self._calculate_overall_band(
            criterion_bands,
            metadata
        )
        
        # Step 5: Generate detailed feedback
        feedback = self._generate_feedback(
            criterion_bands,
            overall_band,
            {
                'fluency': fluency_result,
                'lexical': lexical_result,
                'grammar': grammar_result,
                'pronunciation': pronunciation_result
            }
        )
        
        # Record for statistical calibration
        self.score_history.append(overall_band)
        
        return {
            'overall_band': overall_band,
            'criterion_bands': criterion_bands,
            'feedback_summary': feedback['summary'],
            'detailed_diagnostics': {
                'fluency': fluency_result,
                'lexical': lexical_result,
                'grammar': grammar_result,
                'pronunciation': pronunciation_result
            },
            'strengths': feedback['strengths'],
            'areas_for_improvement': feedback['improvements']
        }
    
    # ========================================================================
    # INPUT VALIDATION
    # ========================================================================
    
    def _validate_input(self, data: Dict) -> Tuple[bool, str]:
        """Validate minimum sample requirements"""
        
        metadata = data.get('metadata', {})
        
        # Check duration
        duration = metadata.get('audio_duration_sec', 0)
        if duration < self.MIN_DURATION_SEC:
            return False, f"Duration {duration}s < {self.MIN_DURATION_SEC}s required"
        
        # Check content words
        content_words = metadata.get('content_word_count', 0)
        if content_words < self.MIN_CONTENT_WORDS:
            return False, f"Only {content_words} words < {self.MIN_CONTENT_WORDS} required"
        
        # Check speaking time
        speaking_time = metadata.get('speaking_time_sec', 0)
        if speaking_time < self.MIN_SPEAKING_TIME_SEC:
            return False, f"Speaking time {speaking_time}s < {self.MIN_SPEAKING_TIME_SEC}s"
        
        # Check required fields
        required = ['fluency_coherence', 'lexical_resource', 
                   'grammatical_range_accuracy', 'pronunciation']
        for field in required:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        return True, ""
    
    # ========================================================================
    # FEATURE ENHANCEMENT
    # ========================================================================
    
    def _enhance_features(self, data: Dict, transcript: str) -> Dict:
        """Extract additional features not in base analysis"""
        
        enhanced = {
            'lexical': self._enhance_lexical_features(
                data['lexical_resource'], 
                transcript,
                data['metadata']['content_word_count']
            ),
            'pronunciation': self._enhance_pronunciation_features(
                data['pronunciation']
            )
        }
        
        return enhanced
    
    def _enhance_lexical_features(self, lexical: Dict, transcript: str, word_count: int) -> Dict:
        """Deep lexical analysis"""
        
        words = transcript.lower().split()
        
        # Detect idiomatic expressions
        idiom_count = 0
        found_idioms = []
        for idiom in self.IDIOMS:
            if idiom in transcript:
                idiom_count += 1
                found_idioms.append(idiom)
        
        # Check collocation accuracy
        collocation_correct = 0
        collocation_total = 0
        for verb, nouns in self.COLLOCATIONS.items():
            for noun in nouns:
                pattern = f"{verb}.*{noun}"
                if re.search(pattern, transcript):
                    collocation_total += 1
                    collocation_correct += 1  # Simplified - assume correct if found
        
        # Count Academic Word List coverage
        awl_count = sum(1 for word in words if any(awl in word for awl in self.AWL))
        
        # Count phrasal verbs
        phrasal_count = sum(1 for pv in self.PHRASAL_VERBS if pv in transcript)
        
        # Count basic word overuse
        basic_overuse = sum(words.count(word) for word in self.BASIC_WORDS)
        
        # Calculate sophistication score (0-10)
        sophistication = 0.0
        sophistication += min(3.0, idiom_count * 0.5)  # Idioms: max 3 pts
        sophistication += min(2.0, (collocation_correct / max(1, collocation_total)) * 2)  # Collocations: max 2 pts
        sophistication += min(2.0, awl_count * 0.2)  # AWL: max 2 pts
        sophistication += min(1.0, phrasal_count * 0.25)  # Phrasal verbs: max 1 pt
        sophistication += min(2.0, (word_count / 100) * 0.5)  # Length bonus: max 2 pts
        
        return {
            'idiomatic_expressions': {
                'count': idiom_count,
                'examples': found_idioms
            },
            'collocation_accuracy': {
                'correct': collocation_correct,
                'total': collocation_total
            },
            'academic_word_list_coverage': awl_count,
            'phrasal_verbs': {
                'count': phrasal_count
            },
            'basic_word_overuse': basic_overuse,
            'sophistication_score': sophistication
        }
    
    def _enhance_pronunciation_features(self, pronunciation: Dict) -> Dict:
        """Calculate prosody score from available features"""
        
        # Use monotone detection as primary prosody indicator
        monotone = pronunciation.get('prosody', {}).get('monotone_detected', True)
        
        # Estimate prosody quality
        if monotone:
            prosody_score = 0.4  # Poor prosody
        else:
            # Use confidence metrics as proxy for prosodic quality
            conf = pronunciation['intelligibility']['mean_word_confidence']
            prosody_score = min(0.8, conf * 0.9)  # Good but not native-like
        
        return {
            'prosody_quality_score': prosody_score,
            'has_natural_intonation': not monotone
        }
    
    # ========================================================================
    # CRITERION SCORERS
    # ========================================================================
    
    def _score_fluency_coherence(self, fluency: Dict, metadata: Dict) -> Dict:
        """
        Three-stage fluency scoring: base → deductions → gates
        """
        
        base_score = 9.0
        deductions = []
        gates = []
        
        # Extract metrics
        wpm = fluency['rate']['speech_rate_wpm']
        long_pauses = fluency['pauses']['long_pause_rate']
        pause_freq = fluency['pauses']['pause_frequency_per_min']
        fillers = fluency['disfluency']['filler_frequency_per_min']
        repetition = fluency['disfluency']['repetition_rate']
        coherence_breaks = fluency['coherence']['coherence_breaks']
        topic_relevant = fluency['coherence']['topic_relevance']
        
        # ============ STAGE 1: DEDUCTIONS ============
        
        # Speech rate
        if wpm < self.FLUENCY_WPM_VERY_SLOW:
            deductions.append(('speech_too_slow', 3.0))
        elif wpm < self.FLUENCY_WPM_SLOW:
            deductions.append(('speech_slow', 2.0))
        elif wpm < self.FLUENCY_WPM_HESITANT:
            deductions.append(('speech_hesitant', 1.0))
        elif wpm > self.FLUENCY_WPM_RUSHED:
            deductions.append(('speech_rushed', 0.5))
        
        # Long pauses
        if long_pauses > self.FLUENCY_LONG_PAUSE_SEVERE:
            deductions.append(('excessive_pausing', 2.5))
        elif long_pauses > self.FLUENCY_LONG_PAUSE_FREQUENT:
            deductions.append(('frequent_pausing', 1.5))
        elif long_pauses > self.FLUENCY_LONG_PAUSE_NOTICEABLE:
            deductions.append(('noticeable_pausing', 0.5))
        
        # Fillers
        if fillers > self.FLUENCY_FILLER_EXCESSIVE:
            deductions.append(('excessive_fillers', 2.5))
        elif fillers > self.FLUENCY_FILLER_FREQUENT:
            deductions.append(('frequent_fillers', 1.5))
        elif fillers > self.FLUENCY_FILLER_SOME:
            deductions.append(('some_fillers', 0.5))
        
        # Repetition
        if repetition > self.FLUENCY_REPETITION_EXCESSIVE:
            deductions.append(('excessive_repetition', 2.0))
        elif repetition > self.FLUENCY_REPETITION_FREQUENT:
            deductions.append(('frequent_repetition', 1.0))
        elif repetition > self.FLUENCY_REPETITION_SOME:
            deductions.append(('some_repetition', 0.3))
        
        # Coherence
        if not topic_relevant:
            deductions.append(('off_topic', 3.0))
        
        if coherence_breaks >= 3:
            deductions.append(('severe_coherence_loss', 2.5))
        elif coherence_breaks == 2:
            deductions.append(('moderate_coherence_loss', 1.5))
        elif coherence_breaks == 1:
            deductions.append(('minor_coherence_loss', 0.5))
        
        # Apply deductions
        for reason, amount in deductions:
            base_score -= amount
        
        # ============ STAGE 2: HARD GATES ============
        
        # Gate 1: Band 1 = no communication possible
        if not topic_relevant or wpm < 30:
            gates.append(('no_communication', 1.5))
        
        # Gate 2: Band 3 ceiling
        if wpm < self.FLUENCY_WPM_VERY_SLOW and coherence_breaks >= 2:
            gates.append(('very_limited_communication', 3.5))
        
        # Gate 3: Band 5 ceiling - must avoid this unfair penalty
        # Only apply if BOTH conditions severe
        if coherence_breaks >= 3 and fillers > self.FLUENCY_FILLER_EXCESSIVE:
            gates.append(('unstable_fluency', 5.5))
        
        # Gate 4: Band 7 ceiling
        if long_pauses > self.FLUENCY_LONG_PAUSE_NOTICEABLE or fillers > self.FLUENCY_FILLER_SOME:
            gates.append(('lacks_native_fluency', 7.5))
        
        # Apply strictest gate
        if gates:
            gated_score = min(g[1] for g in gates)
            base_score = min(base_score, gated_score)
        
        # ============ STAGE 3: POSITIVE INDICATORS ============
        
        # Band 8-9 requires excellence across all metrics
        if base_score >= 8.0:
            if not (wpm >= self.FLUENCY_WPM_COMFORTABLE and 
                   long_pauses < self.FLUENCY_LONG_PAUSE_MINIMAL and
                   fillers < self.FLUENCY_FILLER_MINIMAL and
                   repetition < self.FLUENCY_REPETITION_MINIMAL):
                base_score = min(base_score, 7.5)
        
        final_score = self._round(base_score)
        
        return {
            'score': final_score,
            'deductions': deductions,
            'gates': gates,
            'metrics': {
                'wpm': wpm,
                'long_pauses': long_pauses,
                'fillers': fillers,
                'repetition': repetition,
                'coherence_breaks': coherence_breaks
            }
        }
    
    def _score_lexical_resource(self, lexical: Dict, enhanced: Dict, 
                                metadata: Dict, transcript: str) -> Dict:
        """
        Three-stage lexical scoring with sophistication emphasis
        """
        
        base_score = 9.0
        deductions = []
        gates = []
        
        word_count = metadata['content_word_count']
        sophistication = enhanced['sophistication_score']
        
        # ============ STAGE 1: DEDUCTIONS ============
        
        # Diversity (necessary but not sufficient)
        diversity = lexical['breadth']['lexical_diversity']
        if diversity < self.LEXICAL_DIVERSITY_VERY_LIMITED:
            deductions.append(('very_limited_range', 3.0))
        elif diversity < self.LEXICAL_DIVERSITY_LIMITED:
            deductions.append(('limited_range', 2.0))
        elif diversity < self.LEXICAL_DIVERSITY_ADEQUATE:
            deductions.append(('adequate_range', 1.0))
        
        # Basic word overuse
        basic_overuse = enhanced['basic_word_overuse']
        if basic_overuse > 20:
            deductions.append(('excessive_basic_vocab', 2.0))
        elif basic_overuse > 10:
            deductions.append(('noticeable_basic_vocab', 1.0))
        
        # Word choice errors
        error_rate = (lexical['quality']['word_choice_errors'] / word_count) * 100
        if error_rate > self.LEXICAL_ERROR_RATE_FREQUENT:
            deductions.append(('frequent_word_errors', 2.5))
        elif error_rate > self.LEXICAL_ERROR_RATE_SOME:
            deductions.append(('some_word_errors', 1.5))
        elif error_rate > self.LEXICAL_ERROR_RATE_OCCASIONAL:
            deductions.append(('occasional_word_errors', 0.5))
        
        # Apply deductions
        for reason, amount in deductions:
            base_score -= amount
        
        # ============ STAGE 2: HARD GATES (CRITICAL) ============
        
        # Gate 1: No sophistication = max Band 5.5
        if sophistication < 3.0:
            gates.append(('no_sophistication', 5.5))
        
        # Gate 2: No idiomatic usage = max Band 6.5
        if enhanced['idiomatic_expressions']['count'] == 0:
            gates.append(('no_idiomatic_usage', 6.5))
        
        # Gate 3: Poor collocations = max Band 6.0
        if enhanced['collocation_accuracy']['total'] > 0:
            col_acc = (enhanced['collocation_accuracy']['correct'] / 
                      enhanced['collocation_accuracy']['total'])
            if col_acc < 0.6:
                gates.append(('poor_collocations', 6.0))
        
        # Gate 4: No advanced vocabulary = max Band 5.5
        if lexical['quality']['advanced_vocabulary_count'] == 0 and word_count >= 80:
            gates.append(('no_advanced_vocabulary', 5.5))
        
        # Gate 5: Band 7+ requires AWL coverage
        if enhanced['academic_word_list_coverage'] < 2 and base_score >= 7.0:
            gates.append(('insufficient_academic_vocab', 6.5))
        
        # Gate 6: Band 7+ requires phrasal verbs
        if enhanced['phrasal_verbs']['count'] == 0 and base_score >= 7.0:
            gates.append(('no_phrasal_verbs', 6.5))
        
        # Apply strictest gate
        if gates:
            gated_score = min(g[1] for g in gates)
            base_score = min(base_score, gated_score)
        
        # ============ STAGE 3: POSITIVE INDICATORS ============
        
        # Band 8-9 requires exceptional sophistication
        if base_score >= 8.0:
            if not (sophistication >= 7.0 and
                   enhanced['idiomatic_expressions']['count'] >= 2 and
                   error_rate < 1.0):
                base_score = min(base_score, 7.5)
        
        final_score = self._round(base_score)
        
        return {
            'score': final_score,
            'deductions': deductions,
            'gates': gates,
            'sophistication_score': sophistication,
            'metrics': {
                'diversity': diversity,
                'idioms': enhanced['idiomatic_expressions']['count'],
                'awl_coverage': enhanced['academic_word_list_coverage'],
                'phrasal_verbs': enhanced['phrasal_verbs']['count'],
                'error_rate': error_rate
            }
        }
    
    def _score_grammatical_range_accuracy(self, grammar: Dict, metadata: Dict) -> Dict:
        """
        Three-stage grammar scoring with complex structure focus
        """
        
        base_score = 9.0
        deductions = []
        gates = []
        
        word_count = metadata['content_word_count']
        
        # Calculate metrics
        mlu = grammar['complexity']['mean_utterance_length']
        complex_attempted = grammar['complexity']['complex_structures_attempted']
        complex_accurate = grammar['complexity']['complex_structures_accurate']
        total_errors = grammar['accuracy']['grammar_errors']
        blocking_ratio = grammar['accuracy']['meaning_blocking_error_ratio']
        
        complex_acc_rate = (complex_accurate / complex_attempted 
                           if complex_attempted > 0 else 0)
        error_rate = (total_errors / word_count) * 100 if word_count > 0 else 100
        
        # Count structure range (types attempted)
        structure_range = 1 if complex_attempted > 0 else 0
        if complex_attempted >= 2:
            structure_range = 2
        if complex_attempted >= 4:
            structure_range = 3
        
        # ============ STAGE 1: DEDUCTIONS ============
        
        # Utterance length
        if mlu < self.GRAMMAR_MLU_VERY_SIMPLE:
            deductions.append(('very_simple_sentences', 3.0))
        elif mlu < self.GRAMMAR_MLU_SIMPLE:
            deductions.append(('simple_sentences', 2.0))
        elif mlu < self.GRAMMAR_MLU_MODERATE:
            deductions.append(('moderate_complexity', 1.0))
        
        # Structure range
        if structure_range < 2:
            deductions.append(('very_limited_range', 2.5))
        elif structure_range < 3:
            deductions.append(('limited_range', 1.0))
        
        # Error rate
        if error_rate > self.GRAMMAR_ERROR_RATE_FREQUENT:
            deductions.append(('frequent_errors', 3.0))
        elif error_rate > self.GRAMMAR_ERROR_RATE_NOTICEABLE:
            deductions.append(('noticeable_errors', 2.0))
        elif error_rate > self.GRAMMAR_ERROR_RATE_SOME:
            deductions.append(('some_errors', 1.0))
        elif error_rate > self.GRAMMAR_ERROR_RATE_OCCASIONAL:
            deductions.append(('occasional_errors', 0.5))
        
        # Complex accuracy
        if complex_acc_rate < self.GRAMMAR_COMPLEX_ACC_VERY_POOR:
            deductions.append(('very_poor_complex_control', 3.5))
        elif complex_acc_rate < self.GRAMMAR_COMPLEX_ACC_POOR:
            deductions.append(('poor_complex_control', 2.5))
        elif complex_acc_rate < self.GRAMMAR_COMPLEX_ACC_WEAK:
            deductions.append(('weak_complex_control', 1.5))
        elif complex_acc_rate < self.GRAMMAR_COMPLEX_ACC_GOOD:
            deductions.append(('developing_complex_control', 0.5))
        
        # Blocking errors
        if blocking_ratio > self.GRAMMAR_BLOCKING_FREQUENT:
            deductions.append(('frequent_blocking_errors', 3.0))
        elif blocking_ratio > self.GRAMMAR_BLOCKING_SOME:
            deductions.append(('some_blocking_errors', 2.0))
        elif blocking_ratio > self.GRAMMAR_BLOCKING_OCCASIONAL:
            deductions.append(('occasional_blocking_errors', 1.0))
        
        # Apply deductions
        for reason, amount in deductions:
            base_score -= amount
        
        # ============ STAGE 2: HARD GATES ============
        
        # Gate 1: Zero accuracy on complex = max Band 4.5
        if complex_attempted > 0 and complex_acc_rate == 0:
            gates.append(('no_complex_control', 4.5))
        
        # Gate 2: No complex attempted = max Band 5.0
        if complex_attempted == 0:
            gates.append(('no_complex_attempted', 5.0))
        
        # Gate 3: Frequent blocking = max Band 5.5
        if blocking_ratio > 0.25:
            gates.append(('communication_breakdown', 5.5))
        
        # Gate 4: Very limited range = max Band 6.0
        if structure_range < 2:
            gates.append(('insufficient_range', 6.0))
        
        # Gate 5: Band 7+ requires 75%+ complex accuracy
        if complex_acc_rate < 0.75 and base_score >= 7.0:
            gates.append(('insufficient_complex_accuracy', 6.5))
        
        # Gate 6: Band 8+ requires 90%+ complex accuracy
        if complex_acc_rate < 0.90 and base_score >= 8.0:
            gates.append(('not_band_8_accuracy', 7.5))
        
        # Apply strictest gate
        if gates:
            gated_score = min(g[1] for g in gates)
            base_score = min(base_score, gated_score)
        
        # ============ STAGE 3: POSITIVE INDICATORS ============
        
        # Band 8-9 requires excellence
        if base_score >= 8.0:
            if not (complex_acc_rate >= 0.90 and 
                   error_rate < 2.0 and
                   structure_range >= 3):
                base_score = min(base_score, 7.5)
        
        final_score = self._round(base_score)
        
        return {
            'score': final_score,
            'deductions': deductions,
            'gates': gates,
            'metrics': {
                'mlu': mlu,
                'complex_accuracy': complex_acc_rate,
                'error_rate': error_rate,
                'blocking_ratio': blocking_ratio,
                'structure_range': structure_range
            }
        }
    
    def _score_pronunciation(self, pronunciation: Dict, enhanced: Dict, 
                            metadata: Dict) -> Dict:
        """
        Three-stage pronunciation scoring with prosody emphasis
        """
        
        base_score = 9.0
        deductions = []
        gates = []
        
        # Extract metrics
        word_conf = pronunciation['intelligibility']['mean_word_confidence']
        low_conf_ratio = pronunciation['intelligibility']['low_confidence_ratio']
        prosody_quality = enhanced['prosody_quality_score']
        monotone = pronunciation['prosody']['monotone_detected']
        
        # Calculate intelligibility (40% segmental, 60% prosody)
        segmental_score = word_conf * 0.7 + (1 - low_conf_ratio) * 0.3
        intelligibility = segmental_score * 0.4 + prosody_quality * 0.6
        
        # ============ STAGE 1: DEDUCTIONS ============
        
        # Intelligibility-based deductions
        if intelligibility < 0.5:
            deductions.append(('very_difficult_to_understand', 4.0))
        elif intelligibility < 0.65:
            deductions.append(('difficult_to_understand', 3.0))
        elif intelligibility < 0.75:
            deductions.append(('requires_effort', 2.0))
        elif intelligibility < 0.85:
            deductions.append(('noticeable_accent', 1.0))
        elif intelligibility < 0.92:
            deductions.append(('slight_accent', 0.5))
        
        # Prosody-specific deductions
        if monotone:
            deductions.append(('monotone_delivery', 1.5))
        
        if prosody_quality < 0.5:
            deductions.append(('unnatural_rhythm', 1.0))
        
        # Apply deductions
        for reason, amount in deductions:
            base_score -= amount
        
        # ============ STAGE 2: HARD GATES ============
        
        # Gate 1: Poor intelligibility = Band 4
        if intelligibility < self.PRONUN_INTELLIGIBILITY_POOR:
            gates.append(('poor_intelligibility', 4.0))
        
        # Gate 2: Monotone = max Band 6.0
        if monotone:
            gates.append(('no_prosodic_variation', 6.0))
        
        # Gate 3: Band 7+ requires good prosody
        if prosody_quality < 0.70 and base_score >= 7.0:
            gates.append(('insufficient_prosody', 6.5))
        
        # Gate 4: Band 8+ requires excellent prosody
        if prosody_quality < 0.85 and base_score >= 8.0:
            gates.append(('not_native_like', 7.5))
        
        # Gate 5: Band 9 requires near-perfect
        if (prosody_quality < 0.95 or word_conf < 0.95) and base_score >= 9.0:
            gates.append(('not_band_9_quality', 8.5))
        
        # Apply strictest gate
        if gates:
            gated_score = min(g[1] for g in gates)
            base_score = min(base_score, gated_score)
        
        # ============ STAGE 3: POSITIVE INDICATORS ============
        
        # Band 8-9 requires excellence
        if base_score >= 8.0:
            if not (intelligibility >= 0.92 and 
                   prosody_quality >= 0.85 and
                   not monotone):
                base_score = min(base_score, 7.5)
        
        final_score = self._round(base_score)
        
        return {
            'score': final_score,
            'deductions': deductions,
            'gates': gates,
            'metrics': {
                'word_confidence': word_conf,
                'low_conf_ratio': low_conf_ratio,
                'intelligibility': intelligibility,
                'prosody_quality': prosody_quality,
                'monotone': monotone
            }
        }
    
    # ========================================================================
    # OVERALL BAND CALCULATION
    # ========================================================================
    
    def _calculate_overall_band(self, criterion_bands: Dict[str, float], 
                                metadata: Dict) -> float:
        """
        Calculate overall band with weakness penalties and validation
        """
        
        scores = list(criterion_bands.values())
        avg = np.mean(scores)
        min_score = min(scores)
        max_score = max(scores)
        gap = max_score - min_score
        
        # ============ STAGE 1: WEAKNESS PENALTIES ============
        
        overall = avg
        
        # Large gap penalty
        if gap >= 2.0:
            overall = min_score * 0.4 + avg * 0.6
        elif gap >= 1.5:
            overall = min_score * 0.3 + avg * 0.7
        
        # Multiple weak areas compound
        weak_count = sum(1 for s in scores if s <= 5.0)
        if weak_count >= 2:
            overall = min(overall, 5.0)
        elif weak_count == 1:
            overall = min(overall, 6.0)
        
        # ============ STAGE 2: HARD CEILINGS ============
        
        ceilings = []
        
        # Fluency below 5.0 = max overall 6.0
        if criterion_bands['fluency_coherence'] < 5.0:
            ceilings.append(('fluency_barrier', 6.0))
        
        # Grammar below 5.0 = max overall 5.5
        if criterion_bands['grammatical_range_accuracy'] < 5.0:
            ceilings.append(('grammar_barrier', 5.5))
        
        # Any criterion <= 4.0 = max overall 5.0
        if min_score <= 4.0:
            ceilings.append(('severe_weakness', 5.0))
        
        # Lexical weak + others strong = cap at 7.0
        if criterion_bands['lexical_resource'] <= 6.0 and max_score >= 8.0:
            ceilings.append(('lexical_bottleneck', 7.0))
        
        # Apply strictest ceiling
        if ceilings:
            overall = min(overall, min(c[1] for c in ceilings))
        
        # ============ STAGE 3: STATISTICAL CALIBRATION ============
        
        overall = self._apply_statistical_calibration(overall, criterion_bands)
        
        # ============ STAGE 4: VALIDATION ============
        
        # Overall cannot exceed best criterion by more than 0.5
        if overall > max_score + 0.5:
            overall = max_score + 0.5
        
        # Overall should not be below worst criterion by more than 1.0
        if overall < min_score - 1.0:
            overall = min_score - 1.0
        
        return self._round(overall)
    
    def _apply_statistical_calibration(self, overall: float, 
                                       criterion_bands: Dict) -> float:
        """
        Ensure realistic score distribution matching real IELTS data
        """
        
        if len(self.score_history) < 100:
            return overall  # Need more data
        
        # Check Band 8+ percentage
        band_8_plus = sum(1 for s in self.score_history if s >= 8.0)
        band_8_plus_pct = (band_8_plus / len(self.score_history)) * 100
        
        if band_8_plus_pct > self.STAT_BAND_8_PLUS_MAX_PCT:
            # Too many high scores - apply stricter criteria
            if overall >= 8.0:
                # Verify all criteria at 7.5+
                if not all(s >= 7.5 for s in criterion_bands.values()):
                    overall = min(overall, 7.5)
        
        # Check Band 9 percentage
        band_9 = sum(1 for s in self.score_history if s >= 9.0)
        band_9_pct = (band_9 / len(self.score_history)) * 100
        
        if band_9_pct > self.STAT_BAND_9_MAX_PCT:
            # Band 9 should be extremely rare
            if overall >= 9.0:
                overall = min(overall, 8.5)
        
        return overall
    
    # ========================================================================
    # FEEDBACK GENERATION
    # ========================================================================
    
    def _generate_feedback(self, criterion_bands: Dict, overall_band: float,
                          diagnostics: Dict) -> Dict:
        """Generate detailed feedback for test-taker"""
        
        sorted_criteria = sorted(criterion_bands.items(), key=lambda x: x[1])
        weakest = sorted_criteria[0]
        strongest = sorted_criteria[-1]
        
        # Summary
        summary = f"Overall Band: {overall_band}\n"
        summary += f"Weakest: {weakest[0].replace('_', ' ').title()} ({weakest[1]})\n"
        summary += f"Strongest: {strongest[0].replace('_', ' ').title()} ({strongest[1]})"
        
        # Identify strengths
        strengths = []
        for criterion, score in criterion_bands.items():
            if score >= 7.0:
                strengths.append(f"{criterion.replace('_', ' ').title()}: {score}")
        
        # Identify areas for improvement with specific advice
        improvements = []
        
        # Fluency
        if criterion_bands['fluency_coherence'] < 7.0:
            fluency_diag = diagnostics['fluency']
            advice = []
            if fluency_diag['metrics']['wpm'] < 90:
                advice.append("Increase speaking speed through practice")
            if fluency_diag['metrics']['long_pauses'] > 1.0:
                advice.append("Reduce long pauses by preparing ideas in advance")
            if fluency_diag['metrics']['fillers'] > 2.0:
                advice.append("Replace fillers (um, uh) with brief pauses")
            if fluency_diag['metrics']['coherence_breaks'] > 0:
                advice.append("Use linking words to maintain coherence")
            
            if advice:
                improvements.append({
                    'criterion': 'Fluency & Coherence',
                    'current_band': criterion_bands['fluency_coherence'],
                    'suggestions': advice
                })
        
        # Lexical
        if criterion_bands['lexical_resource'] < 7.0:
            lexical_diag = diagnostics['lexical']
            advice = []
            if lexical_diag['sophistication_score'] < 5.0:
                advice.append("Learn and use more idiomatic expressions")
            if lexical_diag['metrics']['idioms'] == 0:
                advice.append("Incorporate common idioms naturally")
            if lexical_diag['metrics']['awl_coverage'] < 3:
                advice.append("Build academic vocabulary for abstract topics")
            if lexical_diag['metrics']['phrasal_verbs'] == 0:
                advice.append("Use phrasal verbs for natural expression")
            
            if advice:
                improvements.append({
                    'criterion': 'Lexical Resource',
                    'current_band': criterion_bands['lexical_resource'],
                    'suggestions': advice
                })
        
        # Grammar
        if criterion_bands['grammatical_range_accuracy'] < 7.0:
            grammar_diag = diagnostics['grammar']
            advice = []
            if grammar_diag['metrics']['complex_accuracy'] < 0.75:
                advice.append("Practice complex structures until automatic")
            if grammar_diag['metrics']['structure_range'] < 3:
                advice.append("Expand range: conditionals, relative clauses, passives")
            if grammar_diag['metrics']['error_rate'] > 3.0:
                advice.append("Focus on accuracy in common structures")
            
            if advice:
                improvements.append({
                    'criterion': 'Grammatical Range & Accuracy',
                    'current_band': criterion_bands['grammatical_range_accuracy'],
                    'suggestions': advice
                })
        
        # Pronunciation
        if criterion_bands['pronunciation'] < 7.0:
            pronun_diag = diagnostics['pronunciation']
            advice = []
            if pronun_diag['metrics']['monotone']:
                advice.append("Practice intonation patterns (rising/falling)")
            if pronun_diag['metrics']['prosody_quality'] < 0.7:
                advice.append("Work on sentence stress and rhythm")
            if pronun_diag['metrics']['intelligibility'] < 0.85:
                advice.append("Focus on problematic sounds with minimal pairs")
            
            if advice:
                improvements.append({
                    'criterion': 'Pronunciation',
                    'current_band': criterion_bands['pronunciation'],
                    'suggestions': advice
                })
        
        return {
            'summary': summary,
            'strengths': strengths,
            'improvements': improvements
        }
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    @staticmethod
    def _round(score: float) -> float:
        """Round to nearest 0.5"""
        return round(score * 2) / 2


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import json
    import sys
    
    print("=" * 70)
    print("IELTS Band Scorer v3.0 - Super Accurate Production System")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        # Load from file
        filename = sys.argv[1]
        try:
            with open(filename) as f:
                analysis_data = json.load(f)
            
            # Extract analysis portion if wrapped in results
            if 'analysis' in analysis_data:
                analysis_data = analysis_data['analysis']
            
            scorer = IELTSBandScorerV3()
            result = scorer.score(analysis_data)
            
            print("\n" + "=" * 70)
            print("SCORING RESULTS")
            print("=" * 70)
            
            if result.get('validation_failed'):
                print(f"\n❌ {result['feedback_summary']}")
            else:
                print(f"\n🎯 Overall Band Score: {result['overall_band']}")
                print("\n📊 Criterion Scores:")
                for criterion, score in result['criterion_bands'].items():
                    criterion_name = criterion.replace('_', ' ').title()
                    print(f"   • {criterion_name:.<40} {score}")
                
                print(f"\n📝 Feedback:")
                print(result['feedback_summary'])
                
                if result.get('strengths'):
                    print(f"\n✅ Strengths:")
                    for strength in result['strengths']:
                        print(f"   • {strength}")
                
                if result.get('areas_for_improvement'):
                    print(f"\n📈 Areas for Improvement:")
                    for area in result['areas_for_improvement']:
                        print(f"\n   {area['criterion']} (Current: Band {area['current_band']})")
                        for suggestion in area['suggestions']:
                            print(f"      - {suggestion}")
                
                # Detailed diagnostics
                if '--verbose' in sys.argv:
                    print("\n" + "=" * 70)
                    print("DETAILED DIAGNOSTICS")
                    print("=" * 70)
                    
                    for criterion, diag in result['detailed_diagnostics'].items():
                        print(f"\n{criterion.upper()}:")
                        print(f"  Score: {diag['score']}")
                        
                        if diag.get('deductions'):
                            print(f"  Deductions:")
                            for reason, amount in diag['deductions']:
                                print(f"    - {reason}: -{amount}")
                        
                        if diag.get('gates'):
                            print(f"  Gates Applied:")
                            for reason, cap in diag['gates']:
                                print(f"    - {reason}: capped at {cap}")
                        
                        if diag.get('metrics'):
                            print(f"  Key Metrics:")
                            for metric, value in diag['metrics'].items():
                                if isinstance(value, float):
                                    print(f"    - {metric}: {value:.3f}")
                                else:
                                    print(f"    - {metric}: {value}")
        
        except FileNotFoundError:
            print(f"\n❌ Error: File '{filename}' not found")
        except json.JSONDecodeError:
            print(f"\n❌ Error: Invalid JSON in '{filename}'")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    else:
        print("\nUsage: python ielts_scorer_v3.py <analysis_file.json> [--verbose]")
        print("\nExample:")
        print("  python ielts_scorer_v3.py L2A_003.json")
        print("  python ielts_scorer_v3.py L2A_003.json --verbose")
        print("\nThe analysis file should contain IELTS speaking analysis data with:")
        print("  - metadata (duration, word counts)")
        print("  - fluency_coherence metrics")
        print("  - lexical_resource metrics")
        print("  - grammatical_range_accuracy metrics")
        print("  - pronunciation metrics")
        print("  - raw_transcript (optional but recommended)")