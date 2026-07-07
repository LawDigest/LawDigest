'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Navbar, NavbarContent, NavbarItem, NavbarBrand } from '@nextui-org/navbar';
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { siteConfig } from '@/config/site';
import { IconNavBorder } from '@/public/svgs';
import {
  SearchBarButton,
  GoBackButton,
  SettingButton,
  SearchButton,
  NotificationButton,
  ThemeSwitchButton,
} from '@/components/common';
import Logo from './Logo';

// IconNavBorder(그라디언트 알약) SVG 폭(px)
const NAV_INDICATOR_WIDTH = 100;
// 라우트 전환 시 Header가 리마운트되어도 직전 활성 인덱스를 유지하기 위한 모듈 레벨 상태(싱글턴)
let navPrevActiveIndex: number | null = null;
// SSR에서 useLayoutEffect 경고를 피하기 위한 isomorphic 처리
const useIsomorphicLayoutEffect = typeof window !== 'undefined' ? useLayoutEffect : useEffect;

export default function Header({
  logo,
  goBack,
  title,
  setting,
  search,
  notification,
  theme,
}: {
  logo?: boolean;
  goBack?: boolean;
  title?: string;
  setting?: boolean;
  search?: boolean;
  notification?: boolean;
  theme?: boolean;
}) {
  const pathname = usePathname();
  const { navItems } = siteConfig;
  const [toggleSearch, setToggleSearch] = useState(false);
  const isTimelineOrFollowing = pathname.startsWith('/timeline') || pathname.startsWith('/following');

  const onClickSearch = useCallback(() => {
    setToggleSearch(!toggleSearch);
  }, [toggleSearch]);

  // 데스크톱/태블릿 상단 내비 활성 인디케이터(그라디언트 알약) 슬라이드 처리
  const navListRef = useRef<HTMLUListElement | null>(null);
  const navItemRefs = useRef<Array<HTMLAnchorElement | null>>([]);
  const indicatorRef = useRef<HTMLLIElement | null>(null);
  // 이 인스턴스 마운트 직전의 활성 인덱스(모듈 값)를 렌더 시점에 1회 캡처 → 이펙트 재실행(Strict Mode)에 무관하게 고정
  const seedPrevRef = useRef<number | null | undefined>(undefined);
  if (seedPrevRef.current === undefined) {
    seedPrevRef.current = navPrevActiveIndex;
  }
  // 인디케이터가 현재 배치된 인덱스(중복/Strict Mode 2회차 실행 가드)
  const placedIndexRef = useRef<number | null>(null);

  const activeIndex = navItems.findIndex(({ href }) =>
    pathname === '/' ? href === '/' : href !== '/' && pathname.startsWith(href),
  );

  // 활성 항목의 중심에 맞춘 인디케이터 left 오프셋(px)을 DOM 측정으로 계산
  const measureLeft = useCallback((index: number): number | null => {
    const list = navListRef.current;
    const item = navItemRefs.current[index];
    if (!list || !item) return null;
    const listRect = list.getBoundingClientRect();
    const itemRect = item.getBoundingClientRect();
    const itemCenter = itemRect.left - listRect.left + itemRect.width / 2;
    return itemCenter - NAV_INDICATOR_WIDTH / 2;
  }, []);

  // 활성 메뉴 변경(라우트 전환에 따른 리마운트 포함) 시 인디케이터를 이전 위치 → 새 위치로 슬라이드
  // rAF 대신 명령형 DOM 조작 + 강제 reflow로 처리해 Strict Mode 2회 실행/배치 타이밍에 견고
  useIsomorphicLayoutEffect(() => {
    const el = indicatorRef.current;

    if (activeIndex < 0) {
      if (el) el.style.opacity = '0';
      placedIndexRef.current = activeIndex;
      navPrevActiveIndex = activeIndex;
      return;
    }

    // 이미 같은 인덱스로 배치했으면(주로 Strict Mode 2회차) 재실행하지 않음
    if (placedIndexRef.current === activeIndex) return;

    const target = measureLeft(activeIndex);
    if (target === null || !el) return;

    // 최초 마운트면 직전 라우트 인덱스(모듈 캡처값)에서, 이후엔 직전 배치 인덱스에서 시작
    const from = placedIndexRef.current === null ? seedPrevRef.current ?? null : placedIndexRef.current;

    if (from !== null && from >= 0 && from !== activeIndex) {
      const start = measureLeft(from) ?? target;
      el.style.transition = 'none';
      el.style.transform = `translate(${start}px, -50%)`;
      el.style.opacity = '1';
      el.getBoundingClientRect(); // 시작값을 렌더 파이프라인에 확정
      el.style.transition = ''; // className의 트랜지션 사용
      el.style.transform = `translate(${target}px, -50%)`; // 목표로 슬라이드
    } else {
      // 최초 로드 또는 동일 인덱스: 애니메이션 없이 배치
      el.style.transition = 'none';
      el.style.transform = `translate(${target}px, -50%)`;
      el.style.opacity = '1';
      el.getBoundingClientRect();
      el.style.transition = '';
    }

    placedIndexRef.current = activeIndex;
    navPrevActiveIndex = activeIndex;
  }, [activeIndex, measureLeft]);

  // 뷰포트/컨테이너 크기 변화 시 활성 위치로 재정렬(애니메이션 없이 스냅)
  useEffect(() => {
    const snapToActive = () => {
      if (activeIndex < 0) return;
      const el = indicatorRef.current;
      const target = measureLeft(activeIndex);
      if (target === null || !el) return;
      el.style.transition = 'none';
      el.style.transform = `translate(${target}px, -50%)`;
      el.style.opacity = '1';
      el.getBoundingClientRect();
      el.style.transition = '';
    };

    window.addEventListener('resize', snapToActive);

    let observer: ResizeObserver | undefined;
    if (navListRef.current && typeof ResizeObserver !== 'undefined') {
      let skipFirst = true;
      observer = new ResizeObserver(() => {
        if (skipFirst) {
          skipFirst = false;
          return;
        }
        snapToActive();
      });
      observer.observe(navListRef.current);
    }

    return () => {
      window.removeEventListener('resize', snapToActive);
      observer?.disconnect();
    };
  }, [activeIndex, measureLeft]);

  return (
    <section className="w-full">
      <Navbar
        position="static"
        className={`dark:bg-dark-b dark:lg:bg-dark-pb md:h-[98px] dark:border-dark-l ${isTimelineOrFollowing ? 'md:border-b' : 'border-b'}`}>
        <NavbarBrand className="hidden xl:absolute xl:left-[-100px] lg:block">
          <Link href="/">
            <Logo width={106} height={18} />
          </Link>
        </NavbarBrand>

        {logo && (
          <NavbarBrand className="lg:hidden">
            <Link href="/">
              <Logo width={106} height={18} />
            </Link>
          </NavbarBrand>
        )}

        {goBack && (
          <NavbarContent justify="start" className="lg:hidden">
            <NavbarItem>
              <GoBackButton />
            </NavbarItem>
          </NavbarContent>
        )}

        <NavbarContent justify="center" className="hidden mx-auto md:block">
          <ul ref={navListRef} className="relative flex justify-between md:min-w-[430px] w-full gap-2 px-10 lg:gap-20">
            <li
              ref={indicatorRef}
              aria-hidden="true"
              className="pointer-events-none absolute left-0 top-1/2 z-10 list-none transition-transform duration-[450ms] ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none"
              style={{ opacity: 0, transform: 'translate(0px, -50%)' }}>
              <IconNavBorder />
            </li>
            {navItems.map(({ label, href }, index) => {
              const isActive = index === activeIndex;

              return (
                <NavbarItem key={label} className="flex items-center justify-center ">
                  <Link
                    ref={(el) => {
                      navItemRefs.current[index] = el;
                    }}
                    className={`${isActive ? 'text-black dark:text-white font-semibold bg-transparent' : 'text-gray-2'} flex flex-col items-center justify-center text-sm lg:text-base font-medium lg:px-5 lg:py-3 bg-white lg:dark:bg-dark-pb dark:bg-dark-b w-[110px] h-[60px] leading-[60px]`}
                    href={href}>
                    {label}
                  </Link>
                </NavbarItem>
              );
            })}
          </ul>
        </NavbarContent>

        {title && (
          <NavbarContent justify="center" className="md:hidden">
            <NavbarItem className="font-medium">{title}</NavbarItem>
          </NavbarContent>
        )}

        {setting && (
          <NavbarContent justify="end" className="xl:absolute xl:right-[-100px]">
            <NavbarItem>
              <ThemeSwitchButton />
            </NavbarItem>
            <NavbarItem>
              <SettingButton />
            </NavbarItem>
          </NavbarContent>
        )}

        {search && (
          <NavbarContent justify="end" className="xl:absolute xl:right-[-100px]">
            <NavbarItem>
              <ThemeSwitchButton />
            </NavbarItem>
            <NavbarItem>
              <SearchButton onClick={onClickSearch} />
            </NavbarItem>
          </NavbarContent>
        )}

        {notification && (
          <NavbarContent justify="end" className="xl:absolute xl:right-[-100px]">
            <NavbarItem>
              <ThemeSwitchButton />
            </NavbarItem>
            <NavbarItem>
              <NotificationButton />
            </NavbarItem>
          </NavbarContent>
        )}

        {theme && (
          <NavbarContent justify="end" className="xl:absolute xl:right-[-100px]">
            <NavbarItem>
              <ThemeSwitchButton />
            </NavbarItem>
          </NavbarContent>
        )}
      </Navbar>

      <div>{toggleSearch && <SearchBarButton />}</div>
    </section>
  );
}
