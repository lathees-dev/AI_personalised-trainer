from django.urls import path
from . import views

app_name = 'AI_trainer'

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home"), 
    path("communication_options/", views.communication_options, name="communication_options"),
    path("grammar-options/", views.grammar_options, name="grammar_options"),  
    path("vocab-options/", views.vocab_options, name="vocab_options"), 
    path("vocab_learn/", views.vocab_learn, name="vocab_learn"),  
    path("vocabulary/", views.vocabulary, name="vocabulary"),  
    path("exercise-options/<str:exercise_type>/",views.exercise_options,name="exercise_options",),
    path("preposition/", views.preposition, name="preposition"),  
    path("articles/", views.articles, name="articles"),
    path("sentence_formation/", views.sentence_formation, name="sentence_formation"),
    path("active_passive/", views.active_passive, name="active_passive"),
    path("direct_indirect/", views.direct_indirect, name="direct_indirect"),
    path("learn/<str:exercise_type>/", views.learn_exercise, name="learn_exercise"),
    path("fillup/<str:question_type>/", views.fillup, name="fillup"),
    path("speaking/", views.speaking, name="speaking"),
    path("generate_speaking_statement/",views.generate_speaking_statement,name="generate_speaking_statement",),
    path("conjunctions/", views.conjunctions, name="conjunctions"),
    path("interjections/", views.interjections, name="interjections"),
    path("nouns/", views.nouns, name="nouns"),
    path("pronouns/", views.pronouns, name="pronouns"),
    path("tenses/", views.tenses, name="tenses"),
    path("verbs_adverbs/", views.verbs_adverbs, name="verbs_adverbs"),
    path("adjectives/", views.adjectives, name="adjectives"),
    path("mock_test/<str:exercise_type>/", views.mock_test, name="mock_test"),
    path('mock_test_submit/<str:exercise_type>/', views.handle_mock_test_submit, name='mock_test_submit'),
    path('mixed_mock_test/', views.mixed_mock_test, name='mixed_mock_test'),
    path('mixed_mock_test_submit/', views.handle_mixed_mock_test_submit, name='mixed_mock_test_submit'),


]