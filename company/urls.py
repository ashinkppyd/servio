from django.urls import path

from .views import (
    AllSitesView,
    CompanySitesView,
    CreateSiteView,
    DeleteSiteView,
    SiteReportView,
    UpdateSiteView,
)

urlpatterns = [
    path("create-site/", CreateSiteView.as_view()),
    path("my-sites/", CompanySitesView.as_view()),
    path("all-sites/", AllSitesView.as_view()),
    path("delete-site/<int:site_id>/", DeleteSiteView.as_view()),
    path("update-site/<int:id>/", UpdateSiteView.as_view()),
    path("site-report/<int:site_id>/", SiteReportView.as_view()),
]
