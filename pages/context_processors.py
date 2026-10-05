from .company import company_context


def company(request):
    return {"company": company_context()}
