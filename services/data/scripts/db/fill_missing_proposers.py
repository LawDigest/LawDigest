import sys
import os

# src 모듈 임포트를 위한 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from lawdigest_data.connectors.DatabaseManager import DatabaseManager
from lawdigest_data.bills.DataFetcher import DataFetcher

# ==========================================
# [TEST DB CONFIGURATION]
# 테스트 모드(--test-mode) 사용 시 아래 변수에 접속 정보를 입력하세요.
# ==========================================
# 테스트 DB 설정 (환경변수 또는 하드코딩된 값 사용)
TEST_DB_HOST = os.environ.get("TEST_DB_HOST", "140.245.74.246")
TEST_DB_PORT = int(os.environ.get("TEST_DB_PORT", 2812))
TEST_DB_USER = os.environ.get("TEST_DB_USER", "root")
TEST_DB_PASSWORD = os.environ.get("TEST_DB_PASSWORD", "eLL-@hjm3K7CgFDV-MKp")
TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "lawTestDB")
# ==========================================

def get_db_manager(test_mode=False):
    """DB 매니저 인스턴스를 반환합니다. 테스트 모드인 경우 별도 설정을 사용합니다."""
    if test_mode:
        print(f"⚠️ [TEST MODE] 테스트 데이터베이스({TEST_DB_HOST}:{TEST_DB_PORT})에 연결합니다.")
        return DatabaseManager(
            host=TEST_DB_HOST,
            port=TEST_DB_PORT,
            username=TEST_DB_USER,
            password=TEST_DB_PASSWORD,
            database=TEST_DB_NAME
        )
    else:
        return DatabaseManager()

def find_missing_bills(db_manager):
    """
    BillProposer 또는 RepresentativeProposer 데이터가 누락된 법안 ID를 찾습니다.
    (Bill 테이블에는 존재하지만 연결 테이블에는 없는 경우)
    """
    print("🔍 누락된 발의자 데이터를 찾고 있습니다...")
    
    # query_public = """
    # SELECT b.bill_id 
    # FROM Bill b
    # LEFT JOIN BillProposer bp ON b.bill_id = bp.bill_id
    # WHERE bp.bill_public_proposer_id IS NULL
    # """
    
    # query_rep = """
    # SELECT b.bill_id 
    # FROM Bill b
    # LEFT JOIN RepresentativeProposer rp ON b.bill_id = rp.bill_id
    # WHERE rp.representative_proposer_id IS NULL
    # """

    # 실제로는 데이터가 많을 수 있으므로 LIMIT를 걸거나 배치로 처리하는 것이 좋을 수 있습니다.
    # 일단은 전체를 조회하도록 작성합니다.
    
    # 1. 공동발의자 누락 확인
    query_missing_public = "SELECT bill_id FROM Bill WHERE bill_id NOT IN (SELECT DISTINCT bill_id FROM BillProposer)"
    # 2. 대표발의자 누락 확인
    query_missing_rep = "SELECT bill_id FROM Bill WHERE bill_id NOT IN (SELECT DISTINCT bill_id FROM RepresentativeProposer)"

    result_public = db_manager.execute_query(query_missing_public)
    result_rep = db_manager.execute_query(query_missing_rep)

    missing_public_ids = {row['bill_id'] for row in result_public} if result_public else set()
    missing_rep_ids = {row['bill_id'] for row in result_rep} if result_rep else set()

    all_missing_ids = missing_public_ids.union(missing_rep_ids)
    
    print(f"   - 공동발의자 누락 추정 법안 수: {len(missing_public_ids)}개")
    print(f"   - 대표발의자 누락 추정 법안 수: {len(missing_rep_ids)}개")
    print(f"   - 총 처리 대상 법안 수: {len(all_missing_ids)}개")
    
    # 일관된 처리를 위해 정렬하여 반환
    return sorted(list(all_missing_ids))

def get_congressman_mapping(db_manager):
    """
    Congressman 테이블에서 (이름, 정당) -> (id, party_id) 등의 매핑 정보를 가져옵니다.
    발의자 API 데이터는 이름(HG_NM)과 정당(POLY_NM) 정보를 줍니다.
    Congressman 테이블: assuming fields like congressman_id, congressman_name, party_name, party_id
    """
    print("running get_congressman_mapping")
    # 실제 컬럼명을 확인해야 함. 일단 유추된 컬럼명으로 작성.
    # 문제: 동명이인이 있을 수 있음. API에서 MONA_CD(congressman_id)를 주는지 확인 필요.
    # DataFetcher.fetch_bills_coactors 코드를 보면 'MONA_CD'를 찾으려고 시도함.
    # 즉, fetch_bills_coactors 결과에는 이미 congressman_id(MONA_CD)가 포함되어 있을 가능성이 높음.
    # 따라서 여기서는 congressman_id -> party_id 매핑만 있어도 충분할 수 있음.
    
    query = "SELECT congressman_id, party_id FROM Congressman"
    results = db_manager.execute_query(query)
    
    if not results:
        print("⚠️ [WARNING] Congressman 테이블 데이터가 없습니다.")
        return {}
    
    # id -> party_id 매핑
    mapping = {row['congressman_id']: row['party_id'] for row in results}
    return mapping

def fetch_and_process_proposers(bill_ids, db_manager):
    """
    누락된 법안 ID에 대해 DataFetcher를 통해 발의자 정보를 수집합니다.
    """
    if not bill_ids:
        return []

    print(f"🚀 {len(bill_ids)}개 법안에 대한 발의자 정보 수집을 시작합니다...")
    
    fetcher = DataFetcher()
    # DataFetcher의 fetch_bills_coactors는 df_bills(billId 컬럼 포함)를 인자로 받거나 직접 수집함.
    # 여기서는 billId 리스트만 있으므로 임시 DataFrame을 만듭니다.
    import pandas as pd
    temp_df = pd.DataFrame({'billId': bill_ids})
    
    # fetch_bills_coactors는 내부적으로 fetch_lawmakers_data를 호출하여 매핑을 시도함.
    # 결과 컬럼: 'billId', 'representativeProposerIdList', 'publicProposerIdList', 'ProposerName'
    # 여기서 IdList에 들어있는 값들이 congressman_id(MONA_CD)임.
    # verbose=True를 전달하여 API 응답 상세 내용을 확인합니다.
    df_coactors = fetcher.fetch_bills_coactors(df_bills=temp_df, verbose=False)
    
    if df_coactors.empty:
        print("⚠️ 수집된 발의자 데이터가 없습니다.")
        return None

    # 결측치 확인 로직
    missing_rep_mask = df_coactors['representativeProposerIdList'].str.len() == 0
    missing_public_mask = df_coactors['publicProposerIdList'].str.len() == 0
    
    if missing_rep_mask.any():
        print(f"⚠️ 경고: 대표발의자가 없는 법안이 {missing_rep_mask.sum()}개 발견되었습니다.")
        print(df_coactors[missing_rep_mask]['billId'].tolist())

    if missing_public_mask.any():
         print(f"⚠️ 경고: 공동발의자가 없는 법안이 {missing_public_mask.sum()}개 발견되었습니다.")
         print(df_coactors[missing_public_mask]['billId'].tolist())

    if not missing_rep_mask.any() and not missing_public_mask.any():
        print("✅ 모든 법안에 대해 대표발의자 및 공동발의자 정보가 정상적으로 존재합니다.")

    return df_coactors

def update_database(db_manager, df_data, congressman_party_map, db_update=False):
    """
    수집된 데이터를 DB에 업데이트합니다.
    """
    if not db_update:
        print("\n🛑 [DRY RUN] DB 업데이트를 건너뜁니다 (--no-db-update).")
        return

    print("\n💾 데이터베이스 업데이트를 시작합니다...")
    
    total_inserted_rep = 0
    total_inserted_public = 0
    
    for _, row in df_data.iterrows():
        bill_id = row['billId']
        rep_ids = row['representativeProposerIdList'] # list of ids
        pub_ids = row['publicProposerIdList'] # list of ids
        
        bill_rep_count = 0
        bill_pub_count = 0
        
        # RepresentativeProposer Insert
        for rep_id in rep_ids:
             # party_id 찾기
            party_id = congressman_party_map.get(rep_id)
            if party_id is None:
                print(f"   ⚠️ [SKIP] ID {rep_id} (법안 {bill_id})의 Party ID를 찾을 수 없습니다. (Congressman 테이블 누락 가능성)")
                continue
            
            try:
                sql = """
                INSERT INTO RepresentativeProposer (bill_id, congressman_id, party_id, created_date, modified_date)
                VALUES (%s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE modified_date = NOW()
                """
                db_manager.execute_query(sql, (bill_id, rep_id, party_id))
                bill_rep_count += 1
            except Exception as e:
                print(f"   ❌ [ERROR] Representative Insert Failed ({bill_id}, {rep_id}): {e}")

        # BillProposer Insert
        for pub_id in pub_ids:
            party_id = congressman_party_map.get(pub_id)
            if party_id is None:
                continue
                
            try:
                sql = """
                INSERT INTO BillProposer (bill_id, congressman_id, party_id, created_date, modified_date)
                VALUES (%s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE modified_date = NOW()
                """
                db_manager.execute_query(sql, (bill_id, pub_id, party_id))
                bill_pub_count += 1
            except Exception as e:
                print(f"   ❌ [ERROR] Public Proposer Insert Failed ({bill_id}, {pub_id}): {e}")
        
        total_inserted_rep += bill_rep_count
        total_inserted_public += bill_pub_count
        print(f"   - [{bill_id}] 업데이트: 대표 {bill_rep_count}명, 공동 {bill_pub_count}명 추가됨")

    print("\n✅ 업데이트 완료.")
    print(f"   - RepresentativeProposer 총 추가: {total_inserted_rep}건")
    print(f"   - BillProposer 총 추가: {total_inserted_public}건")

def main(no_db_update=False, test_mode=False, limit=0, cross_test_mode=False):
    """
    Args:
        no_db_update (bool): True면 DB 업데이트를 수행하지 않음 (Dry run)
        test_mode (bool): True면 테스트 DB 사용 (읽기/쓰기 모두)
        limit (int): 처리할 법안 최대 개수 (0이면 전체)
        cross_test_mode (bool): True면 Prod DB에서 읽어서 Test DB에 씀 (테스트용)
    """
    
    if cross_test_mode:
        print("🔀 [CROSS TEST MODE] 운영 DB에서 데이터를 읽어 테스트 DB에 업데이트합니다.")
        read_db_manager = get_db_manager(test_mode=False) # Prod
        write_db_manager = get_db_manager(test_mode=True) # Test
        if not read_db_manager.connection:
             print("❌ 운영 DB(Source) 연결에 실패하여 종료합니다.")
             return
        if not write_db_manager.connection:
             print("❌ 테스트 DB(Target) 연결에 실패하여 종료합니다.")
             read_db_manager.close()
             return
    else:
        db_manager = get_db_manager(test_mode)
        read_db_manager = db_manager
        write_db_manager = db_manager
        if not db_manager.connection:
            print("❌ DB 연결에 실패하여 종료합니다.")
            return

    try:
        # 1. 누락된 법안 찾기 (Source DB)
        missing_bill_ids = find_missing_bills(read_db_manager)
        
        if not missing_bill_ids:
            print("✅ 누락된 데이터가 없습니다.")
            return

        if limit > 0:
            print(f"ℹ️  LIMIT 설정으로 인해 {len(missing_bill_ids)}개 중 {limit}개만 처리합니다.")
            missing_bill_ids = missing_bill_ids[:limit]

        # 2. Congressman 정보 가져오기 (Source DB) - 매핑 생성용
        congressman_map = get_congressman_mapping(read_db_manager)
        print(f"ℹ️  {len(congressman_map)}명의 의원 정보를 로드했습니다.")

        # 3. 데이터 수집
        # DataFetcher는 DB와 무관하게 동작하거나 내부적으로 처리함.
        # 인자로 전달되는 db_manager는 현재 사용되지 않음 (None으로 전달해도 무방하나 호환성 유지)
        df_proposers = fetch_and_process_proposers(missing_bill_ids, read_db_manager)
        
        if df_proposers is None or len(df_proposers) == 0:
             print("⚠️ 처리할 데이터가 없습니다 (수집 실패).")
             return

        print("\n📊 수집된 데이터 샘플 (상위 5개):")
        print(df_proposers.head(5))
        print("-" * 50)

        # 4. DB 업데이트 (Target DB)
        update_database(write_db_manager, df_proposers, congressman_map, db_update=not no_db_update)
        
    finally:
        read_db_manager.close()
        if cross_test_mode:
            write_db_manager.close()

if __name__ == "__main__":
    # 여기서 파라미터를 직접 수정하여 실행할 수 있습니다.
    # cross_test_mode=False: 운영 DB에 직접 업데이트
    # limit=5: 5개만 먼저 시도
    main(no_db_update=False, test_mode=False, limit=0, cross_test_mode=False)

