from fpdf import FPDF

def create_test_pdf(path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', size=14)
    pdf.multi_cell(0, 10, '이 문서는 RAG-AI 테스트용 PDF 파일입니다.\n\n'
                      '내용 요약 기능, 검색, 자연어 기반 워크플로우를 검증합니다.\n'
                      '이메일 발송이 스케줄될 수 있습니다.\n'
                      '테스트 날짜: 2026-01-11\n'
                      'AI 기반 요약 시스템 End-to-End 테스트입니다.')
    pdf.output(path)

if __name__ == "__main__":
    import os
    os.makedirs('tests/test_resources', exist_ok=True)
    create_test_pdf('tests/test_resources/aaa.PDF')
    print('테스트 PDF 생성 완료!')
