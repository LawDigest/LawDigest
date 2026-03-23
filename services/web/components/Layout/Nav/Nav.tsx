'use client';

import { useEffect, useLayoutEffect, useState, useCallback, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useRecoilValue } from 'recoil';
import { siteConfig } from '@/config/site';
import { searchModalState } from '@/store';

const SHELL_PADDING_PX = 4;

const SEARCH_SUGGESTIONS = [
  '최근 통과된 주요 법안은?',
  '의료법 개정안 진행 상황이 궁금해요',
  '이번 회기 국회 일정 알려줘',
];

function Nav() {
  const { navItems } = siteConfig;
  const pathname = usePathname();
  const router = useRouter();
  const [isCompact, setIsCompact] = useState(false);
  const [lastScrollTop, setLastScrollTop] = useState(0);
  const searchModal = useRecoilValue(searchModalState);

  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const isSearchOpenRef = useRef(false);

  const navRef = useRef<HTMLElement | null>(null);

  const activeIndex = navItems.findIndex(({ href }) =>
    pathname === '/' ? href === '/' : href !== '/' && pathname.startsWith(href),
  );

  const activeIndexRef = useRef(activeIndex);
  useEffect(() => {
    activeIndexRef.current = activeIndex;
  }, [activeIndex]);

  const setNavIndex = useCallback((index: number) => {
    navRef.current?.style.setProperty('--mobile-nav-index', String(index));
  }, []);

  useLayoutEffect(() => {
    if (activeIndex >= 0) setNavIndex(activeIndex);
  }, [activeIndex, setNavIndex]);

  // 드래그 상태
  const dragState = useRef<{
    isDragging: boolean;
    startX: number;
    startIndex: number;
    lastX: number;
  } | null>(null);
  const isDraggingRef = useRef(false);
  const wasDraggingRef = useRef(false);
  const [isDragging, setIsDragging] = useState(false);

  // 검색 열기/닫기
  const openSearch = useCallback(() => {
    setIsSearchOpen(true);
    isSearchOpenRef.current = true;
    setIsCompact(false);
  }, []);

  const closeSearch = useCallback(() => {
    setIsSearchOpen(false);
    isSearchOpenRef.current = false;
    setSearchQuery('');
  }, []);

  const handleSearchSubmit = useCallback(
    (query: string) => {
      if (!query.trim()) return;
      router.push(`/search/${encodeURIComponent(query.trim())}`);
      closeSearch();
    },
    [router, closeSearch],
  );

  // 검색창 열릴 때 input focus
  useEffect(() => {
    if (isSearchOpen) {
      const timer = setTimeout(() => searchInputRef.current?.focus(), 220);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [isSearchOpen]);

  // compact 전환 시 is-nav-transitioning 클래스
  const isFirstCompactRender = useRef(true);
  useEffect(() => {
    if (isFirstCompactRender.current) {
      isFirstCompactRender.current = false;
      return undefined;
    }
    const nav = navRef.current;
    if (!nav) return undefined;
    nav.classList.add('is-nav-transitioning');
    const timer = setTimeout(() => nav.classList.remove('is-nav-transitioning'), 340);
    return () => {
      clearTimeout(timer);
      nav.classList.remove('is-nav-transitioning');
    };
  }, [isCompact]);

  // 드래그 중 페이지 스크롤 차단
  const registerNavRef = useCallback((node: HTMLElement | null) => {
    navRef.current = node;
    if (!node) return;
    const idx = activeIndexRef.current >= 0 ? activeIndexRef.current : 0;
    node.style.setProperty('--mobile-nav-index', String(idx));
    const onTouchMove = (e: TouchEvent) => {
      if (isDraggingRef.current) e.preventDefault();
    };
    node.addEventListener('touchmove', onTouchMove, { passive: false });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 스크롤 감지 (compact 전환) — 검색/드래그 중 차단
  useEffect(() => {
    const handleScroll = (event: WheelEvent) => {
      if (isDraggingRef.current || isSearchOpenRef.current) return;
      setIsCompact(event.deltaY > 0);
    };
    const handleTouchMove = (event: TouchEvent) => {
      if (isDraggingRef.current || isSearchOpenRef.current) return;
      const currentTouch = event.touches[0].clientY;
      setIsCompact(currentTouch < lastScrollTop);
      setLastScrollTop(currentTouch <= 0 ? 0 : currentTouch);
    };
    window.addEventListener('wheel', handleScroll, true);
    window.addEventListener('touchmove', handleTouchMove, true);
    return () => {
      window.removeEventListener('wheel', handleScroll, true);
      window.removeEventListener('touchmove', handleTouchMove, true);
    };
  }, [lastScrollTop]);

  // 드래그 핸들러
  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    wasDraggingRef.current = false;
    dragState.current = {
      isDragging: false,
      startX: e.clientX,
      startIndex: activeIndexRef.current >= 0 ? activeIndexRef.current : 0,
      lastX: e.clientX,
    };
  }, []);

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      const drag = dragState.current;
      if (!drag) return;

      const deltaX = e.clientX - drag.startX;

      if (!drag.isDragging && Math.abs(deltaX) > 8) {
        drag.isDragging = true;
        isDraggingRef.current = true;
        wasDraggingRef.current = true;
        setIsDragging(true);
        (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
      }

      if (!drag.isDragging) return;
      drag.lastX = e.clientX;

      const nav = navRef.current;
      if (!nav) return;
      const navRect = nav.getBoundingClientRect();
      const innerWidth = navRect.width - SHELL_PADDING_PX * 2;
      const tabWidth = innerWidth / navItems.length;
      const fracIndex = Math.max(0, Math.min(navItems.length - 1, drag.startIndex + deltaX / tabWidth));
      setNavIndex(fracIndex);
    },
    [navItems.length, setNavIndex],
  );

  const handlePointerUp = useCallback(() => {
    const drag = dragState.current;
    if (!drag) return;
    dragState.current = null;
    isDraggingRef.current = false;

    if (!drag.isDragging) {
      setIsDragging(false);
      return;
    }

    const nav = navRef.current;
    if (!nav) return;
    const navRect = nav.getBoundingClientRect();
    const deltaX = drag.lastX - drag.startX;
    const innerWidth = navRect.width - SHELL_PADDING_PX * 2;
    const tabWidth = innerWidth / navItems.length;
    const targetIndex = Math.max(0, Math.min(navItems.length - 1, drag.startIndex + Math.round(deltaX / tabWidth)));

    setIsDragging(false);
    window.requestAnimationFrame(() => setNavIndex(targetIndex));
    router.push(navItems[targetIndex].href);
  }, [navItems, router, setNavIndex]);

  const isSearchActive = pathname.startsWith('/search') || searchModal.show;

  return (
    <>
      {/* 검색 열림 시 백드롭 — 탭하면 닫힘 */}
      {isSearchOpen && <div className="mobile-floating-nav-backdrop" onClick={closeSearch} aria-hidden="true" />}

      <div
        className="mobile-floating-nav-wrapper"
        style={{ '--mobile-nav-count': navItems.length } as React.CSSProperties}>
        {/* 탭 바 */}
        <nav
          ref={registerNavRef}
          className={`mobile-floating-nav${isCompact ? ' is-compact' : ''}${isDragging ? ' is-dragging' : ''}${isSearchOpen ? ' is-search-open' : ''}`}
          onPointerDown={isSearchOpen ? undefined : handlePointerDown}
          onPointerMove={isSearchOpen ? undefined : handlePointerMove}
          onPointerUp={isSearchOpen ? undefined : handlePointerUp}
          onPointerCancel={
            isSearchOpen
              ? undefined
              : () => {
                  dragState.current = null;
                  isDraggingRef.current = false;
                  setIsDragging(false);
                }
          }>
          <div className="mobile-floating-nav__indicator" />

          <div aria-hidden="true" className="mobile-floating-nav__active-overlay">
            {navItems.map(({ label, IconComponent }) => (
              <div key={label} className="mobile-floating-nav__item is-active" style={{ pointerEvents: 'none' }}>
                <IconComponent isActive />
                <span>{label}</span>
              </div>
            ))}
          </div>

          {navItems.map(({ label, href, IconComponent }, index) => (
            <button
              key={label}
              type="button"
              className="mobile-floating-nav__item"
              onClick={() => {
                if (!wasDraggingRef.current) {
                  setNavIndex(index);
                  setIsCompact(false);
                  router.push(href);
                }
                wasDraggingRef.current = false;
              }}
              aria-current={activeIndex === index ? 'page' : undefined}>
              <IconComponent isActive={false} />
              <span>{label}</span>
            </button>
          ))}

          {/* 검색 열림 시: 현재 활성 탭 아이콘만 단독 표시 (클릭 시 검색 닫힘) */}
          {navItems.map(({ label, IconComponent }, i) =>
            i === activeIndex ? (
              <button
                key={`solo-${label}`}
                type="button"
                className="mobile-floating-nav__solo-icon is-active"
                onClick={closeSearch}
                aria-label="검색 닫기">
                <IconComponent isActive />
              </button>
            ) : (
              <div key={`solo-${label}`} className="mobile-floating-nav__solo-icon" aria-hidden="true">
                <IconComponent isActive />
              </div>
            ),
          )}
        </nav>

        {/* 검색 그룹: 예시 질문 버블 + 검색 버튼/바 */}
        <div className="mobile-floating-nav-search-group">
          {/* 예시 질문 버블 */}
          <div className={`mobile-floating-nav-suggestions${isSearchOpen ? ' is-visible' : ''}`}>
            {SEARCH_SUGGESTIONS.map((suggestion, i) => (
              <button
                key={suggestion}
                type="button"
                className="mobile-floating-nav-suggestion"
                style={{ '--suggestion-delay': `${i * 0.06}s` } as React.CSSProperties}
                onClick={() => handleSearchSubmit(suggestion)}>
                {suggestion}
              </button>
            ))}
          </div>

          {/* 검색 버튼 / 확장 검색 바 */}
          <div
            className={`mobile-floating-nav-search-wrap${isSearchActive ? ' is-active' : ''}${isCompact ? ' is-compact' : ''}${isSearchOpen ? ' is-expanded' : ''}`}>
            {/* 확장 상태: 검색 입력 영역 */}
            <div className="mobile-floating-nav-search-expanded-inner">
              <svg
                className="mobile-floating-nav-search-expanded-icon"
                width="18"
                height="18"
                viewBox="0 0 22 22"
                fill="none"
                xmlns="http://www.w3.org/2000/svg">
                <circle cx="9.5" cy="9.5" r="6" stroke="currentColor" strokeWidth="1.7" />
                <path d="M14 14L19 19" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
              </svg>
              <form
                className="mobile-floating-nav-search-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSearchSubmit(searchQuery);
                }}>
                <input
                  ref={searchInputRef}
                  className="mobile-floating-nav-search-input"
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="궁금한 입법 현황을 질문해 보세요"
                  autoComplete="off"
                />
              </form>
              <button
                type="button"
                className="mobile-floating-nav-search-close"
                onClick={closeSearch}
                aria-label="검색 닫기">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M1 1L13 13M13 1L1 13" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                </svg>
              </button>
            </div>

            {/* 기본 상태: 검색 아이콘 버튼 */}
            <button type="button" onClick={openSearch} aria-label="검색" className="mobile-floating-nav-search-btn">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="9.5" cy="9.5" r="6" stroke="currentColor" strokeWidth="1.7" />
                <path d="M14 14L19 19" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default Nav;
