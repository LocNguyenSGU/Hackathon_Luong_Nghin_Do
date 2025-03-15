from rest_framework import serializers

class TextToSpeechSerializer(serializers.Serializer):
    text = serializers.CharField()
    voice = serializers.ChoiceField(choices=['happy', 'sad', 'neutral'])
