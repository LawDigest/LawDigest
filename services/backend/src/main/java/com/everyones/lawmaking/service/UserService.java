package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.response.UserMyPageInfoResponse;
import com.everyones.lawmaking.domain.entity.User;
import com.everyones.lawmaking.global.error.UserException;
import com.everyones.lawmaking.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {
    private final UserRepository userRepository;

    public User findById(long userId) {
        return userRepository.findById(userId)
                .orElseThrow(() -> new UserException.UserNotFoundException(Map.of("userId", Long.toString(userId))));
    }

    public UserMyPageInfoResponse getUserMyPageInfo(long userId) {
        var user = findById(userId);
        return UserMyPageInfoResponse.from(user);
    }

    public List<User> getUserByLikedBillId(String billId) {
        return userRepository.findAllByBillId(billId);
    }

    public List<User> getUserByLikedCongressmanId(String congressmanId) {
        return userRepository.findAllByCongressmanId(congressmanId);
    }

    public int deleteUserById(Long userId) {
        return userRepository.deleteUserById(userId);
    }

}
